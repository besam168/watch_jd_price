import argparse
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

DEFAULT_REDDIT_FEEDS = {
    "localllama": ("REDDIT LocalLLaMA top week", "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=week"),
    "openai": ("REDDIT OpenAI top week", "https://www.reddit.com/r/OpenAI/top/.rss?t=week"),
    "chatgpt": ("REDDIT ChatGPT top week", "https://www.reddit.com/r/ChatGPT/top/.rss?t=week"),
    "promptengineering": ("REDDIT PromptEngineering top week", "https://www.reddit.com/r/PromptEngineering/top/.rss?t=week"),
    "machinelearning": ("REDDIT MachineLearning top week", "https://www.reddit.com/r/MachineLearning/top/.rss?t=week"),
    "artificial": ("REDDIT artificial top week", "https://www.reddit.com/r/artificial/top/.rss?t=week"),
}

DEFAULT_GITHUB_TOPICS = {
    "ai-agents": ("GITHUB topic ai-agents", "https://github.com/topics/ai-agents"),
    "browser-automation": ("GITHUB topic browser-automation", "https://github.com/topics/browser-automation"),
    "openclaw": ("GITHUB topic openclaw", "https://github.com/topics/openclaw"),
    "memory": ("GITHUB topic memory", "https://github.com/topics/memory"),
    "rag": ("GITHUB topic rag", "https://github.com/topics/rag"),
    "workflow-automation": ("GITHUB topic workflow-automation", "https://github.com/topics/workflow-automation"),
}

TOPIC_PRESETS = {
    "general": {
        "reddit": ["localllama", "openai", "chatgpt"],
        "github": ["ai-agents", "browser-automation"],
    },
    "agent": {
        "reddit": ["localllama", "openai", "artificial"],
        "github": ["ai-agents", "workflow-automation"],
    },
    "browser-automation": {
        "reddit": ["localllama", "chatgpt"],
        "github": ["browser-automation", "ai-agents"],
    },
    "memory": {
        "reddit": ["localllama", "machinelearning"],
        "github": ["memory", "rag"],
    },
    "openclaw": {
        "reddit": ["localllama", "promptengineering"],
        "github": ["openclaw", "ai-agents"],
    },
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "have", "has", "are", "you", "your", "about",
    "into", "what", "when", "where", "their", "will", "just", "been", "than", "then", "they", "them",
    "http", "https", "www", "reddit", "github", "week", "top", "using", "used", "over", "under",
    "openai", "chatgpt", "localllama", "machinelearning", "artificial", "promptengineering",
    "topic", "agent", "agents", "automation", "browser", "memory", "openclaw", "workflow", "rag"
}

REPO_HINTS = {
    "agent": ["agent", "agents", "assistant", "workflow", "orchestr", "task", "tool"],
    "browser-automation": ["browser", "playwright", "automation", "scrape", "crawler", "web"],
    "memory": ["memory", "rag", "retriev", "vector", "knowledge", "context"],
    "openclaw": ["openclaw", "agent", "skill", "automation", "tool"],
    "general": ["agent", "automation", "memory", "browser", "workflow"],
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def sanitize_topic(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "general"


def default_output_path(topic: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return Path(__file__).resolve().parent.parent / f"patrol-run-{sanitize_topic(topic)}-{today}.txt"


def default_summary_path(topic: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return Path(__file__).resolve().parent.parent / f"patrol-summary-{sanitize_topic(topic)}-{today}.md"


def resolve_topic_config(topic: str):
    key = topic.lower().strip()
    preset = TOPIC_PRESETS.get(key)
    if preset:
        return preset
    return TOPIC_PRESETS["general"]


def pick_reddit_sources(topic: str, selected: str):
    if selected == "custom":
        key = topic.lower().strip()
        return [key] if key in DEFAULT_REDDIT_FEEDS else []
    preset = resolve_topic_config(topic)
    return preset["reddit"] if selected in ("both", "reddit") else []


def pick_github_sources(topic: str, selected: str):
    if selected == "custom":
        key = topic.lower().strip()
        return [key] if key in DEFAULT_GITHUB_TOPICS else []
    preset = resolve_topic_config(topic)
    return preset["github"] if selected in ("both", "github") else []


def fetch_reddit_entries(label: str, url: str, limit: int = 5):
    entries_out = []
    try:
        xml_text = fetch(url)
        root = ET.fromstring(xml_text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = root.findall("a:entry", ns)[:limit]
        for entry in entries:
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
            link_el = entry.find("a:link", ns)
            href = link_el.attrib.get("href", "") if link_el is not None else ""
            entries_out.append({"source": label, "title": title, "url": href})
    except Exception as e:
        entries_out.append({"source": label, "title": f"ERROR: {type(e).__name__}: {e}", "url": ""})
    return entries_out


def fetch_github_repos(label: str, url: str, limit: int = 12):
    repos_out = []
    try:
        html = fetch(url)
        repo_matches = re.findall(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', html)
        repos = []
        banned_prefixes = (
            "topics/", "features/", "enterprise", "collections/", "trending", "marketplace",
            "orgs/", "users/", "settings/", "account/", "site/", "github/", "sponsors/", "login"
        )
        for repo in repo_matches:
            if repo in repos:
                continue
            if any(repo.startswith(prefix) for prefix in banned_prefixes):
                continue
            repos.append(repo)
        for repo in repos[:limit]:
            repos_out.append({"source": label, "repo": repo, "url": f"https://github.com/{repo}"})
        if not repos_out:
            repos_out.append({"source": label, "repo": "(no repos matched)", "url": ""})
    except Exception as e:
        repos_out.append({"source": label, "repo": f"ERROR: {type(e).__name__}: {e}", "url": ""})
    return repos_out


def collect_patrol(topic: str, source: str, reddit_limit: int, github_limit: int):
    reddit_entries = []
    github_repos = []

    reddit_keys = pick_reddit_sources(topic, source)
    github_keys = pick_github_sources(topic, source)

    for key in reddit_keys:
        label, url = DEFAULT_REDDIT_FEEDS[key]
        reddit_entries.extend(fetch_reddit_entries(label, url, limit=reddit_limit))

    for key in github_keys:
        label, url = DEFAULT_GITHUB_TOPICS[key]
        github_repos.extend(fetch_github_repos(label, url, limit=github_limit))

    if source == "custom":
        key = topic.lower().strip()
        if key in DEFAULT_REDDIT_FEEDS:
            label, url = DEFAULT_REDDIT_FEEDS[key]
            reddit_entries.extend(fetch_reddit_entries(label, url, limit=reddit_limit))
        elif key in DEFAULT_GITHUB_TOPICS:
            label, url = DEFAULT_GITHUB_TOPICS[key]
            github_repos.extend(fetch_github_repos(label, url, limit=github_limit))

    return reddit_entries, github_repos


def build_raw_lines(topic: str, source: str, reddit_entries, github_repos):
    lines = [
        "# self-evolution-radar patrol",
        f"topic: {topic}",
        f"source: {source}",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    if reddit_entries:
        grouped = {}
        for item in reddit_entries:
            grouped.setdefault(item["source"], []).append(item)
        for label, items in grouped.items():
            lines.append(f"=== {label} ===")
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item['title']}")
                if item["url"]:
                    lines.append(f"   {item['url']}")
            lines.append("")
    elif source in ("both", "reddit", "custom"):
        lines.extend(["=== REDDIT ===", "(no configured reddit sources for this topic)", ""])

    if github_repos:
        grouped = {}
        for item in github_repos:
            grouped.setdefault(item["source"], []).append(item)
        for label, items in grouped.items():
            lines.append(f"=== {label} ===")
            for idx, item in enumerate(items, 1):
                lines.append(f"{idx}. {item['url'] or item['repo']}")
            lines.append("")
    elif source in ("both", "github", "custom"):
        lines.extend(["=== GITHUB ===", "(no configured github sources for this topic)", ""])

    return lines


def tokenize_titles(reddit_entries):
    words = []
    for item in reddit_entries:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+-]{2,}", item["title"].lower()):
            if token not in STOPWORDS:
                words.append(token)
    return Counter(words)


def score_repo(repo_name: str, topic: str):
    hints = REPO_HINTS.get(topic.lower().strip(), REPO_HINTS["general"])
    lowered = repo_name.lower()
    return sum(1 for hint in hints if hint in lowered)


def repo_comment(repo_name: str, topic: str):
    lowered = repo_name.lower()
    if topic == "browser-automation" and any(k in lowered for k in ["browser", "playwright", "web", "crawl"]):
        return "和浏览器自动化主线贴得较近，可重点看交互方式与工程结构。"
    if topic == "memory" and any(k in lowered for k in ["memory", "rag", "vector", "context"]):
        return "和 memory / RAG 主线相关，适合看上下文组织与检索接口设计。"
    if topic == "openclaw" and any(k in lowered for k in ["openclaw", "skill", "agent"]):
        return "和 OpenClaw / skill 生态更贴边，值得看封装方式与工作流设计。"
    if any(k in lowered for k in ["agent", "workflow", "automation", "tool"]):
        return "和 agent / workflow 方向较贴近，适合先看 README 与目录结构。"
    return "先保留观察，后续再按实际需求判断是否深读。"


def generate_summary(topic: str, source: str, reddit_entries, github_repos):
    topic_key = topic.lower().strip()
    word_counts = tokenize_titles(reddit_entries)
    hot_words = [w for w, _ in word_counts.most_common(6)]

    ranked_repos = [r for r in github_repos if r.get("repo") and not r["repo"].startswith("ERROR") and not r["repo"].startswith("(")]
    ranked_repos.sort(key=lambda item: (-score_repo(item["repo"], topic_key), item["repo"]))
    deep_reads = ranked_repos[:3]
    noise_repos = ranked_repos[-2:] if len(ranked_repos) >= 5 else []

    lines = []
    lines.append(f"# self-evolution-radar 巡逻摘要 - {topic}")
    lines.append("")
    lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 巡逻主题：`{topic}`")
    lines.append(f"- 来源范围：`{source}`")
    lines.append(f"- Reddit 条目数：{len(reddit_entries)}")
    lines.append(f"- GitHub 候选数：{len(ranked_repos)}")
    lines.append("")

    lines.append("## 1. 本轮巡逻主题")
    lines.append("")
    lines.append(f"本轮围绕 **{topic}** 做了一轮最小真实巡逻，当前仍是 `人做判断 + 脚本拉素材` 的 V1/V2 过渡形态，不是全自动研究平台。")
    lines.append("")

    lines.append("## 2. Reddit 热点与用户痛点")
    lines.append("")
    if reddit_entries:
        if hot_words:
            lines.append(f"- 标题高频词：`{ '`, `'.join(hot_words) }`")
        for item in reddit_entries[:5]:
            lines.append(f"- {item['title']}  ")
            lines.append(f"  来源：{item['source']} | 链接：{item['url']}")
    else:
        lines.append("- 本轮未抓到可用 Reddit 条目。")
    lines.append("")

    lines.append("## 3. GitHub 候选项目 / 候选方向")
    lines.append("")
    if ranked_repos:
        for item in ranked_repos[:6]:
            lines.append(f"- `{item['repo']}` - {item['url']}")
    else:
        lines.append("- 本轮未抓到可用 GitHub repo。")
    lines.append("")

    lines.append("## 4. 值得深读的 3 个重点")
    lines.append("")
    if deep_reads:
        for item in deep_reads:
            lines.append(f"- `{item['repo']}`：{repo_comment(item['repo'], topic_key)}")
    else:
        lines.append("- 当前还没有足够扎实的 repo 候选可列为深读对象。")
    lines.append("")

    lines.append("## 5. 对当前项目可回灌的方法")
    lines.append("")
    fallback_methods = {
        "agent": [
            "把“热点发现”和“候选实现筛选”分成两段输出，避免原始材料和判断混在一起。",
            "后续可给 repo 增加轻量评分字段，例如：贴题度、可复用度、实现清晰度。",
            "可以把本轮摘要固定成模板，逐步形成可比较的巡逻历史。",
        ],
        "browser-automation": [
            "重点看候选 repo 是否把浏览器交互、页面解析、任务编排拆层，便于后续借结构。",
            "后续可单独增加“是否支持 Playwright / headless / cloud browser”的观察字段。",
            "将 Reddit 热点与 GitHub 实现建立一对一映射，减少只看热帖不看落地的偏差。",
        ],
        "memory": [
            "优先关注上下文组织、检索接口与持久层分离方式，避免只追概念词。",
            "后续可以专门给 repo 补“memory / rag / vector / knowledge”标签命中统计。",
            "适合把当前摘要模板扩成“问题 -> 实现 -> 可回灌点”的三段结构。",
        ],
        "openclaw": [
            "优先看 skill 封装粒度与任务触发口径，避免把高变化任务过早硬编码。",
            "后续可以把 topic preset 外置，减少每加一个方向都改 Python。",
            "可以增加输出目录规范，让每轮巡逻结果和摘要天然成对归档。",
        ],
        "general": [
            "把原始巡逻结果和结构化摘要同时保留，方便后续回看与迭代模板。",
            "下一步最适合补轻量评分和 watchlist 外置化，而不是直接冲复杂平台。",
            "继续保持“Reddit 提题，GitHub 解题，最后回灌项目”的固定节奏。",
        ],
    }
    for method in fallback_methods.get(topic_key, fallback_methods["general"]):
        lines.append(f"- {method}")
    lines.append("")

    lines.append("## 6. 不建议追的噪音方向")
    lines.append("")
    if noise_repos:
        for item in noise_repos:
            lines.append(f"- `{item['repo']}`：当前仅从 topic 页面露出，还没有足够证据说明它和本轮主题高度贴合。")
    else:
        lines.append("- 本轮候选不多，暂不强行下“噪音”结论，避免误杀。")
    lines.append("")

    lines.append("## 7. 下一步建议动作")
    lines.append("")
    lines.append("- 先从本摘要列出的 3 个深读候选中挑 1 个做 README 级拆读。")
    lines.append("- 将 `topic preset` 外置成配置文件，减少后续维护成本。")
    lines.append("- 给每轮巡逻补一个统一摘要文件，逐步形成历史对比能力。")
    lines.append("")

    lines.append("## 边界说明")
    lines.append("")
    lines.append("- 这仍然是原型输出，不等于成熟研究系统。")
    lines.append("- 当前摘要主要基于 RSS 标题与 GitHub topic 页面，尚未做深层 README / issue / discussion 解析。")
    lines.append("- 因此结论适合作为“下一步看什么”的导航，不应包装成最终研究结论。")
    lines.append("")

    return lines


def parse_args():
    parser = argparse.ArgumentParser(description="Run a self-evolution radar patrol and optionally generate a summary.")
    parser.add_argument("--topic", default="general", help="Patrol topic preset, e.g. general, agent, browser-automation, memory, openclaw")
    parser.add_argument("--source", choices=["both", "reddit", "github", "custom"], default="both", help="Which source set to use")
    parser.add_argument("--reddit-limit", type=int, default=5, help="How many Reddit entries to keep per feed")
    parser.add_argument("--github-limit", type=int, default=12, help="How many GitHub repos to keep per topic page")
    parser.add_argument("--output", default="", help="Optional raw output file path")
    parser.add_argument("--summary-output", default="", help="Optional markdown summary output file path")
    parser.add_argument("--no-summary", action="store_true", help="Skip generating the markdown summary")
    return parser.parse_args()


def main():
    args = parse_args()
    raw_output_path = Path(args.output) if args.output else default_output_path(args.topic)
    summary_output_path = Path(args.summary_output) if args.summary_output else default_summary_path(args.topic)

    reddit_entries, github_repos = collect_patrol(
        topic=args.topic,
        source=args.source,
        reddit_limit=max(1, args.reddit_limit),
        github_limit=max(1, args.github_limit),
    )

    raw_lines = build_raw_lines(args.topic, args.source, reddit_entries, github_repos)
    raw_output_path.write_text("\n".join(raw_lines), encoding="utf-8")
    print(f"RAW_OUTPUT={raw_output_path}")

    if not args.no_summary:
        summary_lines = generate_summary(args.topic, args.source, reddit_entries, github_repos)
        summary_output_path.write_text("\n".join(summary_lines), encoding="utf-8")
        print(f"SUMMARY_OUTPUT={summary_output_path}")


if __name__ == "__main__":
    main()
