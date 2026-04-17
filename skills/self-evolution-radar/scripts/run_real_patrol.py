import argparse
import re
import urllib.request
import xml.etree.ElementTree as ET
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


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def grab_reddit_rss(label: str, url: str, limit: int = 5):
    lines = [f"=== {label} ==="]
    try:
        xml_text = fetch(url)
        root = ET.fromstring(xml_text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = root.findall("a:entry", ns)[:limit]
        if not entries:
            lines.append("(no entries)")
        for i, entry in enumerate(entries, 1):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
            link_el = entry.find("a:link", ns)
            href = link_el.attrib.get("href", "") if link_el is not None else ""
            lines.append(f"{i}. {title}")
            lines.append(f"   {href}")
    except Exception as e:
        lines.append(f"ERROR: {type(e).__name__}: {e}")
    lines.append("")
    return lines


def grab_github_topic(label: str, url: str, limit: int = 12):
    lines = [f"=== {label} ==="]
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
        if not repos:
            lines.append("(no repos matched)")
        for i, repo in enumerate(repos[:limit], 1):
            lines.append(f"{i}. https://github.com/{repo}")
    except Exception as e:
        lines.append(f"ERROR: {type(e).__name__}: {e}")
    lines.append("")
    return lines


def sanitize_topic(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "general"


def default_output_path(topic: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return Path(__file__).resolve().parent.parent / f"patrol-run-{sanitize_topic(topic)}-{today}.txt"


def resolve_topic_config(topic: str):
    key = topic.lower().strip()
    preset = TOPIC_PRESETS.get(key)
    if preset:
        return preset
    return TOPIC_PRESETS["general"]


def pick_reddit_sources(topic: str, selected: str):
    if selected == "none":
        return []
    if selected == "custom":
        key = topic.lower().strip()
        return [key] if key in DEFAULT_REDDIT_FEEDS else []
    preset = resolve_topic_config(topic)
    return preset["reddit"] if selected == "both" or selected == "reddit" else []


def pick_github_sources(topic: str, selected: str):
    if selected == "none":
        return []
    if selected == "custom":
        key = topic.lower().strip()
        return [key] if key in DEFAULT_GITHUB_TOPICS else []
    preset = resolve_topic_config(topic)
    return preset["github"] if selected == "both" or selected == "github" else []


def build_lines(topic: str, source: str, reddit_limit: int, github_limit: int):
    lines = []
    lines.append(f"# self-evolution-radar patrol")
    lines.append(f"topic: {topic}")
    lines.append(f"source: {source}")
    lines.append(f"generated_at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    reddit_keys = pick_reddit_sources(topic, source)
    github_keys = pick_github_sources(topic, source)

    if source in ("both", "reddit") and not reddit_keys:
        lines.append("=== REDDIT ===")
        lines.append("(no configured reddit sources for this topic)")
        lines.append("")

    if source in ("both", "github") and not github_keys:
        lines.append("=== GITHUB ===")
        lines.append("(no configured github sources for this topic)")
        lines.append("")

    for key in reddit_keys:
        label, url = DEFAULT_REDDIT_FEEDS[key]
        lines += grab_reddit_rss(label, url, limit=reddit_limit)

    for key in github_keys:
        label, url = DEFAULT_GITHUB_TOPICS[key]
        lines += grab_github_topic(label, url, limit=github_limit)

    if source == "custom":
        key = topic.lower().strip()
        if key in DEFAULT_REDDIT_FEEDS:
            label, url = DEFAULT_REDDIT_FEEDS[key]
            lines += grab_reddit_rss(label, url, limit=reddit_limit)
        elif key in DEFAULT_GITHUB_TOPICS:
            label, url = DEFAULT_GITHUB_TOPICS[key]
            lines += grab_github_topic(label, url, limit=github_limit)
        else:
            lines.append("=== CUSTOM ===")
            lines.append("(topic not found in built-in reddit feeds or github topics)")
            lines.append("")

    return lines


def parse_args():
    parser = argparse.ArgumentParser(description="Run a minimal self-evolution radar patrol.")
    parser.add_argument("--topic", default="general", help="Patrol topic preset, e.g. general, agent, browser-automation, memory, openclaw")
    parser.add_argument("--source", choices=["both", "reddit", "github", "custom"], default="both", help="Which source set to use")
    parser.add_argument("--reddit-limit", type=int, default=5, help="How many Reddit entries to keep per feed")
    parser.add_argument("--github-limit", type=int, default=12, help="How many GitHub repos to keep per topic page")
    parser.add_argument("--output", default="", help="Optional output file path")
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output) if args.output else default_output_path(args.topic)
    lines = build_lines(
        topic=args.topic,
        source=args.source,
        reddit_limit=max(1, args.reddit_limit),
        github_limit=max(1, args.github_limit),
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
