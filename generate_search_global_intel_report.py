from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRAPLING_OUTPUT = ROOT / "skills" / "scrapling-openclaw" / "output"
REPORTS_DIR = ROOT / "reports" / "scheduled"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = REPORTS_DIR / "global_intel_formal_report_2026-04-21.txt"

POLITICS_TARGET = 15
FINANCE_TARGET = 10
TECH_TARGET = 5

TECH_KEYWORDS = [
    "ai", "openai", "anthropic", "nvidia", "chip", "chips", "semiconductor", "data center",
    "robot", "robotics", "drone", "moon", "nasa", "space", "satellite", "cerebras",
    "apple ceo", "google", "amazon", "microsoft", "tesla", "biotech", "biology", "quantum",
    "blue origin", "marvell", "broadcom", "model", "llm"
]
FINANCE_KEYWORDS = [
    "market", "markets", "stocks", "stock", "bitcoin", "oil", "etf", "ipo", "economy", "index",
    "aluminum", "price", "prices", "msci", "bond", "bonds", "yield", "yields", "inflation",
    "trade", "tariff", "shipping", "commodity", "commodities", "earnings", "investor", "investors",
    "portfolio", "cash", "fund", "rare earth"
]
POLITICS_KEYWORDS = [
    "iran", "israel", "lebanon", "gaza", "ukraine", "russia", "trump", "ceasefire", "war",
    "military", "defense", "defence", "diplom", "sanction", "president", "prime minister",
    "foreign minister", "supreme court", "arrest", "police", "saudi", "china", "pakistan", "middle east",
    "hezbollah", "tehran", "proxy", "ship", "strait of hormuz", "vessels"
]
NOISE_PATTERNS = [
    "how was your weekend", "attention span", "menopause", "couples", "sundays",
    "k-pop", "bts", "psychologist", "public speaking expert"
]
TECH_NEGATIVE_KEYWORDS = [
    "iran", "hormuz", "ceasefire", "war", "oil", "vessels", "ship", "tehran", "saudi", "gaza", "lebanon",
    "police", "proxy", "proxies", "arson", "jewish sites", "foreign minister", "trump"
]
SITE_TITLE_PATTERNS = [
    "techcrunch | startup and technology news",
    "the verge",
    "wired",
    "mit technology review",
    "ieee spectrum",
    "ars technica",
    "bloomberg markets"
]


def load_json(path: Path):
    encodings = ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be")
    last_error = None
    for encoding in encodings:
        try:
            return json.loads(path.read_text(encoding=encoding))
        except Exception as exc:
            last_error = exc
    print(f"[WARN] failed to parse JSON: {path} :: {last_error}")
    return None


def find_latest(prefix: str) -> Path | None:
    files = sorted(SCRAPLING_OUTPUT.glob(prefix), key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0] if files else None


def fix_mojibake(text: str) -> str:
    replacements = {
        "鈥檚": "’s",
        "鈥": "’",
        "聽": " ",
        "聲": "",
        "Â": "",
        "%��j": "’",
        "r�": "·",
        "�": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def shorten_summary_like_title(title: str) -> str:
    title = title.strip()
    if len(title) <= 110:
        return title
    for sep in [". ", "; ", ": ", " — ", " - "]:
        if sep in title:
            first = title.split(sep)[0].strip()
            if 25 <= len(first) <= 110:
                return first
    words = title.split()
    if len(words) > 16:
        return " ".join(words[:16]).rstrip(",.:;") + "..."
    return title[:107].rstrip() + "..."


def salvage_npr_style_title(title: str) -> str:
    t = title.strip()
    if len(t) <= 110:
        return t
    if any(prefix in t.lower() for prefix in [
        "as the end of", "president trump said", "for 25 years", "the war in gaza", "a rare look at",
        "iran's foreign minister", "u.k. police said", "experts who spent months"
    ]):
        for sep in [". ", "; "]:
            if sep in t:
                first = t.split(sep)[0].strip()
                if 20 <= len(first) <= 140:
                    return first
    return shorten_summary_like_title(t)


def clean_title(title: str) -> str:
    title = fix_mojibake(title)
    title = re.sub(r"\s+", " ", title).strip(" -*•\t\r\n|")
    title = re.sub(r"^(April\s+\d{1,2},\s+\d{4})\s*[·•-]?\s*", "", title, flags=re.I)
    title = re.sub(r"^(Listen\s*[:\-]?\s*)", "", title, flags=re.I)
    title = re.sub(r"^(Watch\s*[:\-]?\s*)", "", title, flags=re.I)
    title = re.sub(r"^In this episode we learn about\s*", "", title, flags=re.I)
    title = salvage_npr_style_title(title)
    title = re.sub(r"\bU\.S\.$", "U.S.", title)
    if len(title) > 140:
        title = title[:137].rstrip() + "..."
    return title.strip()


def looks_like_noise(title: str) -> bool:
    t = title.lower().strip()
    if not t or len(t) < 18:
        return True
    if any(p in t for p in NOISE_PATTERNS):
        return True
    if any(p in t for p in SITE_TITLE_PATTERNS):
        return True
    if t.startswith("have a tip?"):
        return True
    if "send us information securely" in t:
        return True
    if t.endswith("startup and technology news"):
        return True
    if t in {"government & policy", "events", "podcasts", "startups", "venture", "apps"}:
        return True
    return False


def take_titles(payload, limit=10, source_hint: str = ""):
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("headlines") or payload.get("items") or payload.get("results") or []
        if not rows and isinstance(payload.get("sources"), list):
            rows = []
            for source in payload.get("sources", []):
                if isinstance(source, dict):
                    source_name = str(source.get("source") or "")
                    source_rows = source.get("items") or source.get("headlines") or []
                    for item in source_rows:
                        if isinstance(item, dict):
                            item = dict(item)
                            item["_source_hint"] = source_name
                        rows.append(item)
        if not rows and isinstance(payload.get("sites"), list):
            rows = []
            for site in payload.get("sites", []):
                if isinstance(site, dict):
                    rows.extend(site.get("headlines") or site.get("items") or [])
    else:
        rows = []
    out = []
    for row in rows:
        row_source_hint = source_hint
        if isinstance(row, dict):
            title = str(row.get("title") or row.get("headline") or row.get("text") or "").strip()
            row_source_hint = str(row.get("_source_hint") or source_hint)
        else:
            title = str(row).strip()
        title = clean_title(title)
        if row_source_hint == "npr_world":
            title = salvage_npr_style_title(title)
            if len(title) < 25 or title.endswith(" U.S") or title.endswith(" U.S."):
                continue
        if title and not looks_like_noise(title) and title not in out:
            out.append(title)
    return out[:limit]


def classify(title: str) -> str:
    t = title.lower()
    tech_score = sum(1 for k in TECH_KEYWORDS if k in t)
    finance_score = sum(1 for k in FINANCE_KEYWORDS if k in t)
    politics_score = sum(1 for k in POLITICS_KEYWORDS if k in t)

    if any(k in t for k in TECH_NEGATIVE_KEYWORDS):
        tech_score = 0

    if politics_score >= max(tech_score, finance_score) and politics_score > 0:
        return "politics"
    if finance_score >= max(tech_score, politics_score) and finance_score > 0:
        return "finance"
    if tech_score > 0:
        return "tech"
    return "politics"


def summarize_content(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["iran", "hormuz", "israel", "lebanon", "middle east", "gaza", "tehran"]):
        return "中东、航运与能源安全仍在反复影响国际局势和市场风险偏好。"
    if any(k in t for k in ["russia", "ukraine"]):
        return "俄乌线索仍在持续，地缘博弈与制裁预期继续影响欧洲安全与市场。"
    if any(k in t for k in ["china", "tariff", "trade", "saudi", "pakistan"]):
        return "大国协调、资源通道与贸易政策仍在共同影响全球供应链预期。"
    if any(k in t for k in ["market", "stocks", "bitcoin", "msci", "etf", "bond", "yield", "inflation", "cash", "portfolio"]):
        return "市场价格与资金流继续围绕风险偏好、政策预期和地缘变化波动。"
    if any(k in t for k in ["oil", "aluminum", "commodity", "shipping", "rare earth"]):
        return "大宗商品与工业链条正在对地缘冲突和运输风险进行重新定价。"
    if any(k in t for k in ["ai", "openai", "anthropic", "chip", "data center", "drone", "nasa", "moon", "cerebras", "robot", "satellite", "blue origin"]):
        return "AI 与科技产业链继续扩展到算力、模型、军工与太空等关键方向。"
    return "这条新闻反映出全球政治、市场或科技主线仍在继续演变。"


def summarize_comment(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["iran", "hormuz", "oil", "ceasefire", "war"]):
        return "未来24至48小时需看事件与价格信号是否继续强化。"
    if any(k in t for k in ["market", "stocks", "bitcoin", "msci", "etf", "yield", "cash"]):
        return "重点观察资金流和风险偏好是否继续扩散。"
    if any(k in t for k in ["ai", "openai", "anthropic", "chip", "data center", "cerebras", "robot", "satellite"]):
        return "科技主线仍强，后续重点看商业化与估值延续性。"
    return "后续重点看是否出现政策、事件或价格的新确认信号。"


def source_line(source: str) -> str:
    return f"（来源：{source}，发布时间：{datetime.now().strftime('%Y-%m-%d %H:%M +0800')}）"


def build_section(title: str, items: list[tuple[str, str]]) -> str:
    lines = [title]
    for idx, (headline, source) in enumerate(items, start=1):
        lines.append(f"{idx}. 标题：{headline}")
        lines.append(f"内容：{summarize_content(headline)}")
        lines.append(f"评论：{summarize_comment(headline)}")
        lines.append(source_line(source))
    return "\n".join(lines)


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\s+", " ", text)
    return fix_mojibake(text)


def extract_titles_from_html(path: Path, limit: int = 8, source_name: str = "") -> list[str]:
    encodings = ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be")
    text = None
    for encoding in encodings:
        try:
            text = path.read_text(encoding=encoding, errors="replace")
            break
        except Exception:
            continue
    if text is None:
        return []

    candidates = []
    if source_name.lower() == "techcrunch":
        article_patterns = [
            r'title="([^"]{25,180})"',
            r'data-post-title="([^"]{25,180})"',
            r'<a[^>]+href="https://techcrunch.com/[^\"]+"[^>]*>(.*?)</a>',
            r'<h2[^>]*>(.*?)</h2>',
            r'<h3[^>]*>(.*?)</h3>',
        ]
        for pattern in article_patterns:
            for match in re.findall(pattern, text, flags=re.I):
                line = clean_title(strip_html(match))
                low = line.lower()
                if 25 <= len(line) <= 180 and not looks_like_noise(line):
                    if any(bad in low for bad in ["strictlyvc", "download", "government & policy", "events", "podcast", "newsletter"]):
                        continue
                    if low in SITE_TITLE_PATTERNS or line.count("|") > 0:
                        continue
                    candidates.append(line)
    else:
        for pattern in [
            r"<title[^>]*>(.*?)</title>",
            r"<h1[^>]*>(.*?)</h1>",
            r"<h2[^>]*>(.*?)</h2>",
            r"<h3[^>]*>(.*?)</h3>",
            r">([^<>]{20,160})<",
        ]:
            for match in re.findall(pattern, text, flags=re.I):
                line = clean_title(strip_html(match))
                if 15 <= len(line) <= 160 and not looks_like_noise(line):
                    candidates.append(line)

    out = []
    seen = set()
    bad_tokens = ["privacy", "cookie", "subscribe", "sign in", "login", "newsletter", "advertisement"]
    if source_name.lower() == "techcrunch":
        bad_tokens.extend(["strictlyvc", "download", "events", "podcast", "government & policy"])
    for line in candidates:
        low = line.lower()
        if any(token in low for token in bad_tokens):
            continue
        if line not in seen:
            seen.add(line)
            out.append(line)
        if len(out) >= limit:
            break
    return out


def add_source_items(container: list, titles: list[str], source: str, forced_category: str | None = None):
    for title in titles:
        title = clean_title(title)
        if not title or looks_like_noise(title):
            continue
        category = forced_category or classify(title)
        if forced_category == "tech" and any(k in title.lower() for k in TECH_NEGATIVE_KEYWORDS):
            category = classify(title)
        container.append((title, source, category))


def main() -> int:
    sources = []
    mapping = {
        "ap_latest_headlines.json": "AP",
        "probe_cnbc_npr_latest.json": "CNBC/NPR",
        "reuters_via_yahoo_latest.json": "Reuters via Yahoo fallback",
        "probe_bloomberg_latest.json": "Bloomberg Markets",
        "ft_en_headlines_latest.json": "FT.com",
    }
    tech_mapping = {
        "arstechnica": "Ars Technica",
        "ieee": "IEEE Spectrum",
        "wired": "Wired",
        "technologyreview": "MIT Technology Review",
        "theverge": "The Verge",
    }

    for name, source in mapping.items():
        path = SCRAPLING_OUTPUT / name
        payload = load_json(path)
        if payload is None:
            continue
        add_source_items(sources, take_titles(payload, limit=20, source_hint=source), source)

    for key, source in tech_mapping.items():
        path = SCRAPLING_OUTPUT / f"{key}_latest.json"
        titles = []
        payload = load_json(path)
        if payload is not None:
            titles.extend(take_titles(payload, limit=8, source_hint=source))
            if isinstance(payload, dict):
                title = clean_title(str(payload.get("title") or "").strip())
                if title:
                    titles.append(title)
                output_file = payload.get("output_file")
                if output_file:
                    titles.extend(extract_titles_from_html(Path(output_file), limit=8, source_name=source))
                content = str(payload.get("content") or "")
                for line in content.splitlines():
                    line = clean_title(line.strip(" -*•\t"))
                    if 15 <= len(line) <= 140 and not looks_like_noise(line) and line not in titles:
                        titles.append(line)
        else:
            latest_html = find_latest(f"*{key}*get*.html") or find_latest(f"*{key}*.html")
            if latest_html:
                titles.extend(extract_titles_from_html(latest_html, limit=8, source_name=source))
        add_source_items(sources, titles[:8], source, forced_category="tech")

    seen = set()
    politics, finance, tech = [], [], []
    for title, source, category in sources:
        dedupe_key = title.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        item = (title, source)
        if category == "politics" and len(politics) < POLITICS_TARGET:
            politics.append(item)
        elif category == "finance" and len(finance) < FINANCE_TARGET:
            finance.append(item)
        elif category == "tech" and len(tech) < TECH_TARGET:
            tech.append(item)

    for title, source, category in sources:
        item = (title, source)
        if len(politics) < POLITICS_TARGET and item not in politics and category != "tech":
            politics.append(item)
        if len(finance) < FINANCE_TARGET and item not in finance and category != "politics":
            finance.append(item)
        if len(tech) < TECH_TARGET and item not in tech and category == "tech":
            tech.append(item)

    report = [
        f"全球综合情报报告 - {datetime.now().strftime('%Y-%m-%d')}（自动版）",
        f"发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "整理：沈万三",
        "",
        build_section(f"一、国际政治重要头条（{len(politics)}条）", politics[:POLITICS_TARGET]),
        "",
        build_section(f"二、国际财经头条（{len(finance)}条）", finance[:FINANCE_TARGET]),
        "",
        build_section(f"三、AI / 科技新闻（{len(tech)}条）", tech[:TECH_TARGET]),
    ]
    OUT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(OUT_PATH)
    print(json.dumps({
        "politics": len(politics),
        "finance": len(finance),
        "tech": len(tech),
        "total_sources": len(sources)
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
