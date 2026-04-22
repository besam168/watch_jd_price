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


def take_titles(payload, limit=10):
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("headlines") or payload.get("items") or payload.get("results") or []
        if not rows and isinstance(payload.get("sources"), list):
            rows = []
            for source in payload.get("sources", []):
                if isinstance(source, dict):
                    rows.extend(source.get("items") or source.get("headlines") or [])
        if not rows and isinstance(payload.get("sites"), list):
            rows = []
            for site in payload.get("sites", []):
                if isinstance(site, dict):
                    rows.extend(site.get("headlines") or site.get("items") or [])
    else:
        rows = []
    out = []
    for row in rows:
        if isinstance(row, dict):
            title = str(row.get("title") or row.get("headline") or row.get("text") or "").strip()
        else:
            title = str(row).strip()
        if title and title not in out:
            out.append(title)
    return out[:limit]


def classify(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["ai", "openai", "nvidia", "chip", "data center", "drone", "moon", "nasa", "cerebras", "apple ceo", "biology-tuned"]):
        return "tech"
    if any(k in t for k in ["market", "stocks", "bitcoin", "oil", "etf", "ipo", "economy", "index", "aluminum", "price", "msci"]):
        return "finance"
    return "politics"


def summarize_content(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["iran", "hormuz", "israel", "lebanon", "middle east"]):
        return "中东、航运与能源安全仍在反复影响国际局势和市场风险偏好。"
    if any(k in t for k in ["russia", "ukraine"]):
        return "俄乌与俄罗斯相关线索仍在，但当天整体权重明显弱于中东主线。"
    if any(k in t for k in ["china", "tariff", "trade", "saudi"]):
        return "大国协调、资源通道与贸易政策仍在共同影响全球供应链预期。"
    if any(k in t for k in ["market", "stocks", "bitcoin", "msci", "etf"]):
        return "市场价格与资金流继续围绕风险偏好、政策预期和地缘变化波动。"
    if any(k in t for k in ["oil", "aluminum"]):
        return "大宗商品与工业链条正在对地缘冲突和运输风险进行重新定价。"
    if any(k in t for k in ["ai", "openai", "chip", "data center", "drone", "nasa", "moon", "apple ceo", "cerebras"]):
        return "AI 与科技产业链继续扩展到算力、模型、军工与太空等关键方向。"
    return "这条新闻反映出全球政治、市场或科技主线仍在继续演变。"


def summarize_comment(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["iran", "hormuz", "oil"]):
        return "未来24至48小时需看事件与价格信号是否继续强化。"
    if any(k in t for k in ["market", "stocks", "bitcoin", "msci", "etf"]):
        return "重点观察资金流和风险偏好是否继续扩散。"
    if any(k in t for k in ["ai", "openai", "chip", "data center", "cerebras"]):
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
    return text


def extract_titles_from_html(path: Path, limit: int = 8) -> list[str]:
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
    for pattern in [
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
        r"<h2[^>]*>(.*?)</h2>",
        r"<h3[^>]*>(.*?)</h3>",
        r">([^<>]{20,160})<",
    ]:
        for match in re.findall(pattern, text, flags=re.I):
            line = strip_html(match).strip(" -*•\t\r\n")
            if 15 <= len(line) <= 180:
                candidates.append(line)

    out = []
    seen = set()
    bad_tokens = ["privacy", "cookie", "subscribe", "sign in", "login", "newsletter", "advertisement"]
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
        "techcrunch": "TechCrunch",
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
        for title in take_titles(payload, limit=20):
            sources.append((title, source, classify(title)))

    for key, source in tech_mapping.items():
        path = SCRAPLING_OUTPUT / f"{key}_latest.json"
        payload = load_json(path)
        if payload is None:
            continue
        titles = take_titles(payload, limit=8)
        if not titles and isinstance(payload, dict):
            title = str(payload.get("title") or "").strip()
            if title:
                titles.append(title)
            output_file = payload.get("output_file")
            if output_file:
                titles.extend(extract_titles_from_html(Path(output_file), limit=8))
            content = str(payload.get("content") or "")
            for line in content.splitlines():
                line = line.strip(" -*•\t")
                if 15 <= len(line) <= 140 and line not in titles:
                    titles.append(line)
        for title in titles[:8]:
            sources.append((title, source, "tech"))

    seen = set()
    politics, finance, tech = [], [], []
    for title, source, category in sources:
        if title in seen:
            continue
        seen.add(title)
        if category == "politics" and len(politics) < POLITICS_TARGET:
            politics.append((title, source))
        elif category == "finance" and len(finance) < FINANCE_TARGET:
            finance.append((title, source))
        elif category == "tech" and len(tech) < TECH_TARGET:
            tech.append((title, source))

    for title, source, category in sources:
        if len(politics) < POLITICS_TARGET and (title, source) not in politics and category != "tech":
            politics.append((title, source))
        if len(finance) < FINANCE_TARGET and (title, source) not in finance and category != "politics":
            finance.append((title, source))
        if len(tech) < TECH_TARGET and (title, source) not in tech:
            tech.append((title, source))

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
