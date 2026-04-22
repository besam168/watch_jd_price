from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path
from typing import Iterable
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

try:
    from qveris_report_helpers import fetch_news_items as qv_fetch_news_items
except Exception:
    qv_fetch_news_items = None

SENDER = "910633260@qq.com"
AUTH_CODE = "sghqeeeeyuzjbcbb"
RECEIVERS = ["besam168168@gmail.com", "758622673@qq.com"]
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
TIMEOUT_SECONDS = 20
ROOT = Path(__file__).resolve().parent
FIRECRAWL_DIR = ROOT / ".firecrawl"
MULTI_SEARCH_CONFIG = ROOT / "skills" / "itisbig-multi-search-engine" / "config.json"
A_SHARE_HOT_SPOTS_DIR = ROOT / "skills" / "a-share-hot-spots"

RSS_FEEDS = [
    ("AP News", "https://feeds.apnews.com/rss/apf-topnews"),
    ("CNBC World", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
]

STALE_PATTERNS = [
    "GB200发布",
    "日本结束负利率",
    "标普500在5400点",
]

FRESH_MIN_HOURS = 24
FRESH_MAX_HOURS = 48
SEARCH_DISCOVERY_SITES = [
    # 第一优先：稳定、好抓、适合日更
    ("AP News", "apnews.com", ["middle east", "iran", "israel", "gaza", "ukraine", "china trade", "markets"]),
    ("CNBC World", "cnbc.com/world", ["markets", "stocks", "fed", "oil", "china", "macro"]),
    ("Yahoo Finance", "finance.yahoo.com", ["stocks", "futures", "commodities", "gold", "brent", "china trade"]),

    # 第二优先：内容强，按需补抓
    ("Reuters", "reuters.com", ["middle east", "iran", "israel", "gaza", "ukraine", "china trade", "markets", "oil"]),
    ("BBC News", "bbc.com/news", ["iran", "israel", "gaza", "ukraine", "markets", "china"]),
    ("Bloomberg", "bloomberg.com", ["middle east", "iran", "israel", "ukraine", "china", "markets", "oil", "policy"]),
    ("WSJ", "wsj.com", ["middle east", "iran", "israel", "ukraine", "china", "trade", "markets", "fed"]),

    # 第三优先：补充视角
    ("Al Jazeera", "aljazeera.com", ["gaza", "iran", "israel", "middle east"]),
    ("The Guardian", "theguardian.com", ["iran", "gaza", "ukraine", "markets", "china"]),
    ("DW English", "dw.com/en", ["middle east", "iran", "israel", "ukraine", "china trade", "markets"]),
    ("France24", "france24.com", ["middle east", "ukraine", "markets", "china"]),
    ("USA Today", "usatoday.com", ["us", "politics", "economy", "markets"]),
    ("NPR", "npr.org", ["world", "middle east", "ukraine", "economy"]),

    # 科技版块
    ("The Verge", "theverge.com", ["ai", "anthropic", "openai", "nvidia"]),
    ("TechCrunch", "techcrunch.com", ["ai", "robotics", "openai"]),
]
SEARCH_ENGINE_PREFERENCE = ["DuckDuckGo", "Startpage", "Yahoo"]
MAX_SEARCH_ENGINES = 1
MAX_TOPICS_PER_SITE = 2
MAX_DISCOVERY_ITEMS = 18
MAX_EVIDENCE_FETCH = 18
TECH_SOURCE_WHITELIST = {
    "the verge",
    "techcrunch",
    "ieee spectrum",
    "wired",
    "ars technica",
    "mit technology review",
    "venturebeat ai",
    "singularity hub",
    "ai news",
    "engadget",
}


def read_optional(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def read_optional_recent(path: Path, max_age_hours: int = FRESH_MAX_HOURS) -> str:
    if not path.exists():
        return ""
    try:
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        age = dt.datetime.now().astimezone() - mtime
        if age > dt.timedelta(hours=max_age_hours):
            return ""
    except Exception:
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def latest_capture_time(paths: Iterable[Path]) -> str:
    latest: dt.datetime | None = None
    for path in paths:
        try:
            if not path.exists():
                continue
            ts = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        except Exception:
            continue
        if latest is None or ts > latest:
            latest = ts
    if latest is None:
        return "未获取到抓取时间"
    return latest.strftime("%Y-%m-%d %H:%M:%S")


def fetch_cn_hk_market_snapshot() -> dict[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClaw/1.0",
        "Referer": "https://finance.sina.com.cn",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    symbols = {
        "s_sh000001": "shanghai",
        "s_sz399001": "shenzhen",
        "s_sz399006": "chinext",
        "s_sh000688": "star50",
        "rt_hkHSI": "hangseng_rt",
        "int_dji": "dji_sina",
        "int_nasdaq": "ixic_sina",
        "int_sp500": "spx_sina",
        "int_nikkei": "n225_sina",
        "int_ftse": "ftse_sina",
    }
    query = ",".join(symbols.keys())
    out: dict[str, str] = {}
    try:
        req = urllib.request.Request(f"http://hq.sinajs.cn/list={query}", headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("gbk", errors="replace")
    except Exception:
        return out

    for sym, alias in symbols.items():
        m = re.search(rf'hq_str_{re.escape(sym)}="([^"]*)"', raw)
        if not m:
            continue
        parts = m.group(1).split(",")
        if sym.startswith("s_") and len(parts) >= 4:
            current = plausible(parts[1], 1000, 100000)
            change_pct = parts[3].strip()
            if current:
                out[alias] = normalize_numeric_string(current) or current
            if change_pct:
                out[f"{alias}_change"] = change_pct if str(change_pct).endswith("%") else f"{change_pct}%"
        elif sym == "rt_hkHSI" and len(parts) >= 7:
            current = plausible(parts[6], 10000, 40000)
            change_pct = ""
            if len(parts) > 8 and parts[8].strip():
                change_pct = parts[8].strip()
            elif len(parts) > 32 and parts[32].strip():
                change_pct = parts[32].strip()
            if current:
                out[alias] = normalize_numeric_string(current) or current
            if change_pct:
                out[f"{alias}_change"] = change_pct if str(change_pct).endswith("%") else f"{change_pct}%"
        elif sym.startswith("int_") and len(parts) >= 4:
            current = plausible(parts[1], 1000, 100000)
            change_pct = parts[3].strip()
            if current:
                out[alias] = normalize_numeric_string(current) or current
            if change_pct:
                out[f"{alias}_change"] = change_pct if str(change_pct).endswith("%") else f"{change_pct}%"
    return out


def parse_pub_date_to_local(pub_date: str) -> dt.datetime | None:
    if not pub_date:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(pub_date)
        if parsed is None:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone()
    except Exception:
        return None


def is_within_hour_window(pub_date: str, min_hours: int = FRESH_MIN_HOURS, max_hours: int = FRESH_MAX_HOURS) -> bool:
    parsed = parse_pub_date_to_local(pub_date)
    if parsed is None:
        return False
    now = dt.datetime.now().astimezone()
    delta = now - parsed
    return dt.timedelta(hours=min_hours) <= delta <= dt.timedelta(hours=max_hours)


def fetch_rss_items(limit_per_feed: int = 3, min_age_hours: int = FRESH_MIN_HOURS, max_age_hours: int = FRESH_MAX_HOURS) -> list[dict[str, str]]:
    if qv_fetch_news_items is not None:
        try:
            qv_items = qv_fetch_news_items()
            fresh_qv_items = [
                x for x in qv_items
                if x.get("title") and (not x.get("pub_date") or is_within_hour_window(x.get("pub_date", ""), min_age_hours, max_age_hours))
            ]
            if fresh_qv_items:
                return fresh_qv_items[: max(6, limit_per_feed * len(RSS_FEEDS))]
        except Exception:
            pass

    items: list[dict[str, str]] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClaw/1.0",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }

    for source_name, url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read()
            root = ET.fromstring(raw)
            channel = root.find("channel")
            if channel is None:
                continue
            count = 0
            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                description = (item.findtext("description") or "").strip()
                if not title or is_stale(title):
                    continue
                if not is_within_hour_window(pub_date, min_age_hours, max_age_hours):
                    continue
                items.append(
                    {
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "pub_date": pub_date,
                        "summary": description,
                    }
                )
                count += 1
                if count >= limit_per_feed:
                    break
        except Exception:
            continue
    return items


def is_stale(text: str) -> bool:
    text = text or ""
    return any(p in text for p in STALE_PATTERNS)


def find_number(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, flags=re.I)
    return m.group(1).strip() if m else None


def to_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace(',', '').strip())
    except Exception:
        return None


def plausible(value: str | None, low: float, high: float) -> str | None:
    num = to_float(value)
    if num is None:
        return None
    if low <= num <= high:
        return value
    return None


def normalize_numeric_string(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.replace(",", "").strip()
    try:
        num = float(cleaned)
    except Exception:
        return None
    if abs(num) > 1000000:
        return None
    if cleaned.endswith(".0"):
        cleaned = cleaned[:-2]
    return cleaned


def first_plausible(*values: str | None) -> str | None:
    for value in values:
        norm = normalize_numeric_string(value)
        if norm:
            return norm
    return None


def load_multi_search_templates() -> dict[str, str]:
    try:
        data = json.loads(MULTI_SEARCH_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}
    templates: dict[str, str] = {}
    for engine in data.get("engines", []):
        name = str(engine.get("name") or "").strip()
        url = str(engine.get("url") or "").strip()
        if name and url:
            templates[name] = url
    return templates


def fetch_url_text(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClaw/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="ignore")


def extract_search_result_candidates(source_name: str, site: str, html_text: str, priority_topic: str = "") -> list[dict[str, str]]:
    html_text = html.unescape(html_text)
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    patterns = [
        rf'<a[^>]+href="(?P<url>https?://[^\"]*{re.escape(site)}[^\"]*)"[^>]*>(?P<title>.*?)</a>',
        rf'<a[^>]+href="/l/\?kh=-1&amp;uddg=(?P<encoded>https?%3A%2F%2F[^\"]*{re.escape(site).replace("/", "%2F") }[^\"]*)"[^>]*>(?P<title>.*?)</a>',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html_text, flags=re.I | re.S):
            url = match.groupdict().get("url") or urllib.parse.unquote(match.groupdict().get("encoded") or "")
            title = re.sub(r"<[^>]+>", "", match.groupdict().get("title") or "").strip()
            title = re.sub(r"\s+", " ", title)
            if not url or not title or is_stale(title):
                continue
            lower_title = title.lower()
            if priority_topic and priority_topic.lower() not in lower_title:
                important = any(k in lower_title for k in ["iran", "israel", "gaza", "ukraine", "market", "oil", "china", "trade", "ai", "robot"])
                if not important:
                    continue
            if title.lower() in seen:
                continue
            seen.add(title.lower())
            candidates.append({
                "source": source_name,
                "title": title,
                "link": url,
                "pub_date": "搜索发现（待正文交叉验证）",
                "summary": "",
            })
            if len(candidates) >= 2:
                break
        if candidates:
            break
    return candidates


def discover_news_via_multi_search() -> list[dict[str, str]]:
    templates = load_multi_search_templates()
    if not templates:
        return []

    items: list[dict[str, str]] = []
    active_engines = SEARCH_ENGINE_PREFERENCE[:MAX_SEARCH_ENGINES] if MAX_SEARCH_ENGINES > 0 else SEARCH_ENGINE_PREFERENCE
    for engine_name in active_engines:
        template = templates.get(engine_name)
        if not template:
            continue
        for source_name, site, topics in SEARCH_DISCOVERY_SITES:
            active_topics = topics[:MAX_TOPICS_PER_SITE] if MAX_TOPICS_PER_SITE > 0 else topics
            for topic in active_topics:
                query = f"site:{site} {topic} latest"
                encoded = urllib.parse.quote_plus(query)
                url = template.replace("{keyword}", encoded)
                try:
                    page = fetch_url_text(url)
                except Exception:
                    continue
                items.extend(extract_search_result_candidates(source_name, site, page, priority_topic=topic))
                if MAX_DISCOVERY_ITEMS > 0 and len(items) >= MAX_DISCOVERY_ITEMS:
                    return items[:MAX_DISCOVERY_ITEMS]
    return items[:MAX_DISCOVERY_ITEMS] if MAX_DISCOVERY_ITEMS > 0 else items


def fetch_article_preview(url: str) -> str:
    if not url:
        return ""
    try:
        text = fetch_url_text(url)
    except Exception:
        return ""
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 1200:
        text = text[:1200]
    return text


def enrich_news_items_with_evidence(items: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict]:
    enriched: list[dict[str, str]] = []
    stats = {
        "inputCount": len(items),
        "attempted": 0,
        "withEvidence": 0,
        "withoutEvidence": 0,
        "sources": [],
    }
    source_rows: list[dict[str, str | bool]] = []
    for idx, item in enumerate(items, start=1):
        row = dict(item)
        url = (row.get("link") or "").strip()
        should_fetch_evidence = MAX_EVIDENCE_FETCH <= 0 or idx <= MAX_EVIDENCE_FETCH
        preview = ""
        has_evidence = False
        if should_fetch_evidence:
            stats["attempted"] += 1
            preview = fetch_article_preview(url)
            has_evidence = len(preview) >= 180
        row["evidence_preview"] = preview[:280] if preview else ""
        row["has_evidence"] = has_evidence
        if has_evidence and row.get("pub_date", "").startswith("搜索发现"):
            row["pub_date"] = "已抓正文，精确时间待补"
        if has_evidence and not row.get("summary"):
            row["summary"] = preview[:220]
        if has_evidence:
            stats["withEvidence"] += 1
        else:
            stats["withoutEvidence"] += 1
        source_rows.append({
            "source": row.get("source", "未知"),
            "title": row.get("title", "")[:120],
            "url": url,
            "hasEvidence": has_evidence,
        })
        enriched.append(row)
    stats["sources"] = source_rows
    return enriched, stats


def dedupe_news_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    seen_urls: set[str] = set()
    for item in items:
        title = re.sub(r"\s+", " ", (item.get("title") or "").strip())
        link = (item.get("link") or "").strip()
        if not title:
            continue
        title_key = title.lower()
        if title_key in seen_titles:
            continue
        if link and link in seen_urls:
            continue
        if is_stale(title):
            continue
        seen_titles.add(title_key)
        if link:
            seen_urls.add(link)
        out.append(item)
    return out


def collect_market_provider_snapshot() -> dict[str, str]:
    path = ROOT / "reports" / "scheduled" / "qveris_market_snapshot.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    out: dict[str, str] = {}
    stock_ranges = {
        "AAPL": (50, 500),
        "NVDA": (50, 2000),
        "TSLA": (50, 1000),
    }
    for key in ("AAPL", "NVDA", "TSLA"):
        item = data.get(key) or {}
        price = item.get("c") or item.get("price")
        change = item.get("dp")
        low, high = stock_ranges[key]
        price_text = plausible(str(price) if price is not None else None, low, high)
        if price_text is not None:
            out[key.lower()] = price_text
        if change is not None:
            try:
                change_num = float(change)
                if -30 <= change_num <= 30:
                    out[f"{key.lower()}_change"] = f"{change_num:.2f}%"
            except Exception:
                pass

    indices = {
        "SPX": ("spx", 3000, 10000),
        "IXIC": ("ixic", 8000, 30000),
        "DJI": ("dji", 20000, 60000),
        "FTSE": ("ftse", 4000, 15000),
        "N225": ("n225", 15000, 70000),
        "HSI": ("hangseng", 10000, 40000),
        "TWII": ("twse", 10000, 40000),
        "KOSPI": ("kospi", 1500, 4000),
        "DXY": ("dxy", 80, 130),
        "USDCNY": ("usdcny", 5, 10),
    }
    for key, (out_key, low, high) in indices.items():
        item = data.get(key) or {}
        price = item.get("c") or item.get("price")
        change = item.get("dp")
        price_text = plausible(str(price) if price is not None else None, low, high)
        if price_text is not None:
            out[out_key] = price_text
        if change is not None:
            try:
                change_num = float(change)
                if -20 <= change_num <= 20:
                    out[f"{out_key}_change"] = f"{change_num:.2f}%"
            except Exception:
                pass

    brent = data.get("BZUSD") or {}
    if isinstance(brent, dict):
        brent_price = plausible(str(brent.get("price") or brent.get("c")) if (brent.get("price") is not None or brent.get("c") is not None) else None, 20, 200)
        brent_open = plausible(str(brent.get("open") or brent.get("o")) if (brent.get("open") is not None or brent.get("o") is not None) else None, 20, 200)
        brent_low = plausible(str(brent.get("dayLow") or brent.get("l")) if (brent.get("dayLow") is not None or brent.get("l") is not None) else None, 20, 200)
        brent_high = plausible(str(brent.get("dayHigh") or brent.get("h")) if (brent.get("dayHigh") is not None or brent.get("h") is not None) else None, 20, 200)
        if brent_price is not None:
            out["brent_qv"] = brent_price
        if brent_open is not None:
            out["brent_qv_open"] = brent_open
        if brent_low is not None and brent_high is not None:
            out["brent_qv_range"] = f"{brent_low} - {brent_high}"

    gold = data.get("XAUUSD") or {}
    if isinstance(gold, dict):
        gold_price = plausible(str(gold.get("price") or gold.get("c")) if (gold.get("price") is not None or gold.get("c") is not None) else None, 1000, 10000)
        gold_open = plausible(str(gold.get("open") or gold.get("o")) if (gold.get("open") is not None or gold.get("o") is not None) else None, 1000, 10000)
        gold_low = plausible(str(gold.get("dayLow") or gold.get("l")) if (gold.get("dayLow") is not None or gold.get("l") is not None) else None, 1000, 10000)
        gold_high = plausible(str(gold.get("dayHigh") or gold.get("h")) if (gold.get("dayHigh") is not None or gold.get("h") is not None) else None, 1000, 10000)
        if gold_price is not None:
            out["gold_qv"] = gold_price
        if gold_open is not None:
            out["gold_qv_open"] = gold_open
        if gold_low is not None and gold_high is not None:
            out["gold_qv_range"] = f"{gold_low} - {gold_high}"

    wti = data.get("CLUSD") or {}
    if isinstance(wti, dict):
        wti_price = plausible(str(wti.get("price") or wti.get("c")) if (wti.get("price") is not None or wti.get("c") is not None) else None, 20, 200)
        wti_open = plausible(str(wti.get("open") or wti.get("o")) if (wti.get("open") is not None or wti.get("o") is not None) else None, 20, 200)
        wti_low = plausible(str(wti.get("dayLow") or wti.get("l")) if (wti.get("dayLow") is not None or wti.get("l") is not None) else None, 20, 200)
        wti_high = plausible(str(wti.get("dayHigh") or wti.get("h")) if (wti.get("dayHigh") is not None or wti.get("h") is not None) else None, 20, 200)
        if wti_price is not None:
            out["wti_qv"] = wti_price
        if wti_open is not None:
            out["wti_qv_open"] = wti_open
        if wti_low is not None and wti_high is not None:
            out["wti_qv_range"] = f"{wti_low} - {wti_high}"

    return out


def sanitize_report_text(text: str) -> str:
    replacements = {
        "�?": "",
        "过�?2-24小时": "过去24-48小时",
        "补�?": "补充",
        "二�?0字左右总判�?": "二、50字左右总判断",
        "一、重要头条新�?": "一、重要头条新闻",
        "三、全球市场动�?": "三、全球市场动态",
        "四、地缘政治热�?": "四、地缘政治热点",
        "五、全球经济与产业动�?": "五、全球经济与产业动态",
        "六、风险预警（24-48小时短期 / 中期 / 长期�?": "🚨 风险预警",
        "七、投资建�?": "💡 决策建议",
        "【美股�?": "【美股】",
        "【欧洲与亚太股市�?": "【欧洲与亚太股市】",
        "【商品与避险资产�?": "【商品与避险资产】",
        "【中东�?": "【中东】",
        "【俄乌�?": "【俄乌】",
        "【中美关�?/ 东亚政治�?": "【中美关系 / 东亚政治】",
        "【AI / 机器�?/ 科技前沿�?": "【AI / 机器人 / 科技前沿】",
        "【美股科技龙头快照（东方财富/新浪/腾讯，如存在）�?": "【美股科技龙头快照（东方财富/新浪/腾讯，如存在）】",
        "【短期�?": "【短期】",
        "【中期�?": "【中期】",
        "【长期�?": "【长期】",
        "更�?": "更新",
        "动�?": "动态",
        "热�?": "热点",
        "判�?": "判断",
        "建�?": "建议",
        "发�?": "发酵",
        "交�?": "交涉",
        "升�?": "升温",
        "投�?": "投入",
    }
    for old_s, new_s in replacements.items():
        text = text.replace(old_s, new_s)
    return text


def collect_market_snapshot() -> dict[str, str]:
    reuters = read_optional_recent(FIRECRAWL_DIR / "reuters.com.md")
    yahoo = read_optional_recent(FIRECRAWL_DIR / "finance.yahoo.com.md")
    twse = read_optional_recent(FIRECRAWL_DIR / "twse.com.tw-zh-index.html.md")
    jpx = read_optional_recent(FIRECRAWL_DIR / "jpx.co.jp-english.md")
    krx = read_optional_recent(FIRECRAWL_DIR / "global.krx.co.kr-main-main.jsp.md")
    eastmoney = read_optional_recent(FIRECRAWL_DIR / "eastmoney.com.md")

    data: dict[str, str] = {}
    data["spx"] = first_plausible(find_number(reuters, r"SPX\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"
    data["spx_change"] = find_number(reuters, r"SPX\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "今日无重大更新"
    data["ixic"] = first_plausible(find_number(reuters, r"IXIC\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"
    data["ixic_change"] = find_number(reuters, r"IXIC\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "今日无重大更新"
    data["dji"] = first_plausible(find_number(reuters, r"DJI\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"
    data["dji_change"] = find_number(reuters, r"DJI\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "今日无重大更新"
    data["stoxx"] = first_plausible(find_number(reuters, r"STOXX\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"
    data["ftse"] = first_plausible(find_number(reuters, r"FTSE\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"
    data["n225"] = first_plausible(find_number(reuters, r"N225\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"
    data["n225_change"] = find_number(reuters, r"N225\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "今日无重大更新"
    data["es_fut"] = first_plausible(find_number(yahoo, r"S&P Futures\s*([0-9,]+(?:\.[0-9]+)?)")) or "今日无重大更新"

    twse_index = plausible(find_number(twse, r"(?:TAIEX|加權指數|發行量加權股價指數).*?([0-9,]{4,}(?:\.[0-9]+)?)"), 10000, 50000)
    data["twse"] = twse_index or "今日无重大更新"
    jpx_nikkei = plausible(find_number(jpx, r"Nikkei\s*225.*?([0-9,]{4,}(?:\.[0-9]+)?)"), 10000, 70000)
    data["jpx_nikkei"] = jpx_nikkei or "今日无重大更新"
    if krx:
        kospi = plausible(find_number(krx, r"KOSPI[^0-9]*([0-9,]{4,}(?:\.[0-9]+)?)"), 1500, 4000)
        data["kospi"] = kospi or "今日无重大更新"
    else:
        data["kospi"] = "今日无重大更新"
    if eastmoney:
        hs = plausible(find_number(eastmoney, r"恒生指数[^0-9]*([0-9,]{4,}(?:\.[0-9]+)?)"), 10000, 40000)
        data["hangseng"] = hs or "今日无重大更新"
    else:
        data["hangseng"] = "今日无重大更新"

    cn_hk = fetch_cn_hk_market_snapshot()
    if cn_hk.get("spx_sina"):
        data["spx"] = cn_hk["spx_sina"]
        data["spx_change"] = cn_hk.get("spx_sina_change", data.get("spx_change", "今日无重大更新"))
    if cn_hk.get("ixic_sina"):
        data["ixic"] = cn_hk["ixic_sina"]
        data["ixic_change"] = cn_hk.get("ixic_sina_change", data.get("ixic_change", "今日无重大更新"))
    if cn_hk.get("dji_sina"):
        data["dji"] = cn_hk["dji_sina"]
        data["dji_change"] = cn_hk.get("dji_sina_change", data.get("dji_change", "今日无重大更新"))
    if cn_hk.get("ftse_sina"):
        data["ftse"] = cn_hk["ftse_sina"]
        data["ftse_change"] = cn_hk.get("ftse_sina_change", data.get("ftse_change", "今日无重大更新"))
    if cn_hk.get("n225_sina"):
        data["n225"] = cn_hk["n225_sina"]
        data["n225_change"] = cn_hk.get("n225_sina_change", data.get("n225_change", "今日无重大更新"))
    if cn_hk.get("shanghai"):
        data["shanghai"] = cn_hk["shanghai"]
        data["shanghai_change"] = cn_hk.get("shanghai_change", "今日无重大更新")
    if cn_hk.get("shenzhen"):
        data["shenzhen"] = cn_hk["shenzhen"]
        data["shenzhen_change"] = cn_hk.get("shenzhen_change", "今日无重大更新")
    if cn_hk.get("chinext"):
        data["chinext"] = cn_hk["chinext"]
        data["chinext_change"] = cn_hk.get("chinext_change", "今日无重大更新")
    if cn_hk.get("star50"):
        data["star50"] = cn_hk["star50"]
        data["star50_change"] = cn_hk.get("star50_change", "今日无重大更新")
    if cn_hk.get("hangseng_rt"):
        data["hangseng"] = cn_hk["hangseng_rt"]
        data["hangseng_change"] = cn_hk.get("hangseng_rt_change", data.get("hangseng_change", "今日无重大更新"))

    data.update(collect_market_provider_snapshot())
    return data


def clean_range_text(value: str | None) -> str:
    value = clean_summary_text(value or "")
    if not value:
        return "今日无重大更新"
    value = value.replace("--", "-")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def within_numeric_range(value: str | None, low: float, high: float) -> str | None:
    num = to_float(value)
    if num is None:
        return None
    if low <= num <= high:
        return normalize_numeric_string(value)
    return None


def collect_commodity_snapshot() -> dict[str, str]:
    gold = read_optional_recent(FIRECRAWL_DIR / "finance.yahoo.com-quote-GC=F.md")
    brent = read_optional_recent(FIRECRAWL_DIR / "finance.yahoo.com-quote-BZ=F.md")
    wti = read_optional_recent(FIRECRAWL_DIR / "finance.yahoo.com-quote-CL=F.md")

    data: dict[str, str] = {}
    data["gold_last"] = within_numeric_range(find_number(gold, r"Last Price\s*([0-9,]+(?:\.[0-9]+)?)"), 1500, 4500) or "今日无重大更新"
    data["gold_open"] = within_numeric_range(find_number(gold, r"Open\s*([0-9,]+(?:\.[0-9]+)?)"), 1500, 4500) or "今日无重大更新"
    data["gold_range"] = clean_range_text(find_number(gold, r"Day's Range\s*([0-9,.,\- ]+)"))
    data["brent_last"] = within_numeric_range(find_number(brent, r"Last Price\s*([0-9,]+(?:\.[0-9]+)?)"), 20, 200) or "今日无重大更新"
    data["brent_open"] = within_numeric_range(find_number(brent, r"Open\s*([0-9,]+(?:\.[0-9]+)?)"), 20, 200) or "今日无重大更新"
    data["brent_range"] = clean_range_text(find_number(brent, r"Day's Range\s*([0-9,.,\- ]+)"))
    data["wti_last"] = within_numeric_range(find_number(wti, r"Last Price\s*([0-9,]+(?:\.[0-9]+)?)"), 20, 200) or "今日无重大更新"
    data["wti_open"] = within_numeric_range(find_number(wti, r"Open\s*([0-9,]+(?:\.[0-9]+)?)"), 20, 200) or "今日无重大更新"
    data["wti_range"] = clean_range_text(find_number(wti, r"Day's Range\s*([0-9,.,\- ]+)"))
    data["headline_oil"] = "若缺少扎实最新报价，则只保留页面抓取到的区间，不再用旧默认值补洞。"
    qv = collect_market_provider_snapshot()
    if qv.get("gold_qv"):
        qv_gold = within_numeric_range(qv["gold_qv"], 1500, 4500)
        if qv_gold:
            data["gold_last"] = qv_gold
            data["gold_open"] = within_numeric_range(qv.get("gold_qv_open"), 1500, 4500) or data["gold_open"]
            data["gold_range"] = clean_range_text(qv.get("gold_qv_range")) or data["gold_range"]
    if qv.get("brent_qv"):
        data["brent_last"] = within_numeric_range(qv.get("brent_qv"), 20, 200) or data["brent_last"]
        data["brent_open"] = within_numeric_range(qv.get("brent_qv_open"), 20, 200) or data["brent_open"]
        data["brent_range"] = clean_range_text(qv.get("brent_qv_range")) or data["brent_range"]
    if qv.get("wti_qv"):
        data["wti_last"] = within_numeric_range(qv.get("wti_qv"), 20, 200) or data["wti_last"]
        data["wti_open"] = within_numeric_range(qv.get("wti_qv_open"), 20, 200) or data["wti_open"]
        data["wti_range"] = clean_range_text(qv.get("wti_qv_range")) or data["wti_range"]
    return data


def collect_geopolitical_snapshot() -> dict[str, list[str]]:
    bbc = read_optional_recent(FIRECRAWL_DIR / "bbc.com-news.md")
    reuters = read_optional_recent(FIRECRAWL_DIR / "reuters.com.md")
    reuters_europe = read_optional_recent(FIRECRAWL_DIR / "reuters.com-world-europe.md")
    reuters_china = read_optional_recent(FIRECRAWL_DIR / "reuters.com-world-china.md")
    ap = read_optional_recent(FIRECRAWL_DIR / "apnews.com.md")
    aljazeera = read_optional_recent(FIRECRAWL_DIR / "aljazeera.com.md")

    middle_east: list[str] = []
    russia_ukraine: list[str] = []
    us_china: list[str] = []

    if "hazardous materials incident" in bbc:
        middle_east.append("BBC：以色列称伊朗袭击后南部工业设施起火，并宣布 hazardous materials incident，说明打击已波及工业与次生安全风险。")
    if "major industrial sites hit" in bbc:
        middle_east.append("BBC：海湾工业设施继续遇袭，阿联酋与巴林工业站点受影响。")
    if "Red Sea shipping" in bbc:
        middle_east.append("BBC：胡塞武装对红海航运的潜在威胁仍可能扩大对全球经济的冲击。")
    if "second attack from Yemen" in reuters:
        middle_east.append("Reuters：以色列报告再次遭到来自也门方向的袭击，中东战事仍在外溢。")
    if "Iran" in reuters and ("rescues airman" in reuters or "downed" in reuters):
        middle_east.append("Reuters：美伊冲突相关军事行动升级，说明中东风险仍处高位，不宜简单视作无重大更新。")
    if "Kuwait says Indian worker killed" in aljazeera:
        middle_east.append("Al Jazeera：科威特称一名印度工人在伊朗对电力/水务设施袭击中死亡，冲突已触及民生基础设施。")
    if "Iran rejects Trump's 'helpless, nervous' 48-hour ultimatum" in aljazeera:
        middle_east.append("Al Jazeera：伊朗拒绝美方最后通牒式表态，显示中东局势仍在政治与军事双线升级。")
    if "Alarms activated in Israel's north" in aljazeera:
        middle_east.append("Al Jazeera：以色列北部再响警报，说明战火外溢风险仍在扩散。")
    if "gaza" in aljazeera.lower() or "gaza" in bbc.lower() or "gaza" in reuters.lower() or "gaza" in ap.lower():
        middle_east.append("加沙：本轮抓取仍可见加沙相关关键词，中东主线不能简单判作空白。")
    if "Iran-backed Houthis" in ap:
        middle_east.append("AP：胡塞力量卷入月度冲突并可能进一步威胁全球航运。")

    if "Zelenskiy discusses security partnership" in reuters_europe:
        russia_ukraine.append("Reuters Europe：泽连斯基与约旦国王讨论安全合作，说明俄乌议题仍在牵动更广泛地区外交。")
    if "territorial violation by drones" in reuters_europe:
        russia_ukraine.append("Reuters Europe：芬兰报告无人机疑似越界，且至少一架来自乌克兰方向，外围安全风险上升。")
    if "British diplomat" in reuters_europe:
        russia_ukraine.append("Reuters Europe：俄方以间谍指控驱逐英国外交官，俄欧关系仍紧。")

    if "factory activity seen returning to expansion" in reuters_china:
        us_china.append("Reuters China：中国3月制造业活动或重回扩张区间，说明内需与出口边际修复仍在观察窗口。")
    if "Hong Kong" in reuters_china:
        us_china.append("Reuters China：中国就香港安全规则变更问题对美方表态提出抗议。")
    if "trade practices" in reuters_china:
        us_china.append("Reuters China：中国已对美国贸易做法启动调查，中美经贸摩擦仍有升温空间。")

    return {
        "middle_east": list(dict.fromkeys(middle_east)),
        "russia_ukraine": russia_ukraine,
        "us_china": us_china,
    }


def collect_tech_snapshot() -> list[str]:
    sources = [
        ("The Verge", read_optional_recent(FIRECRAWL_DIR / "theverge.com.md")),
        ("TechCrunch", read_optional_recent(FIRECRAWL_DIR / "techcrunch.com.md")),
        ("IEEE Spectrum", read_optional_recent(FIRECRAWL_DIR / "spectrum.ieee.org.md")),
        ("Wired", read_optional_recent(FIRECRAWL_DIR / "wired.com.md")),
        ("Ars Technica", read_optional_recent(FIRECRAWL_DIR / "arstechnica.com.md")),
        ("MIT Technology Review", read_optional_recent(FIRECRAWL_DIR / "technologyreview.com.md")),
        ("VentureBeat AI", read_optional_recent(FIRECRAWL_DIR / "venturebeat.com-category-ai.md")),
        ("Singularity Hub", read_optional_recent(FIRECRAWL_DIR / "singularityhub.com.md")),
        ("AI News", read_optional_recent(FIRECRAWL_DIR / "artificialintelligence-news.com.md")),
        ("Engadget", read_optional_recent(FIRECRAWL_DIR / "engadget.com.md")),



    ]

    rules = [
        (("openai", "gpt"), "AI大模型仍是科技主线，OpenAI相关进展继续牵引行业预期。"),
        (("anthropic",), "Anthropic 动向仍值得跟踪，模型竞争与企业级应用落地继续推进。"),
        (("google", "gemini"), "Google Gemini 相关进展显示大模型竞争仍在加速，云与终端协同值得关注。"),
        (("tesla", "robot"), "机器人与自动化主题继续升温，硬件量产与真实场景落地是关键观察点。"),
        (("nvidia",), "算力与AI基础设施仍是产业链核心主线，NVIDIA 相关动态继续影响资本开支预期。"),
        (("chip",), "半导体与算力芯片仍是科技投资主轴，供给约束和需求扩张并存。"),
        (("robot",), "机器人赛道热度延续，市场更关注从演示走向商用部署的兑现速度。"),
        (("ai",), "AI 应用层与模型层仍持续放量，重点看真实付费场景和企业采用节奏。"),
    ]

    lines: list[str] = []
    seen: set[str] = set()
    for source_name, text in sources:
        raw = text.lower()
        if not raw:
            continue
        for keywords, zh_line in rules:
            if all(k in raw for k in keywords) and zh_line not in seen:
                lines.append(f"{source_name}：{zh_line}")
                seen.add(zh_line)
                break
        if len(lines) >= 5:
            break
    return lines or ["今日无重大更新"]


def enforce_tech_source_whitelist(lines: list[str]) -> list[str]:
    filtered: list[str] = []
    for line in lines or []:
        if not line or line == "今日无重大更新":
            continue
        m = re.match(r"^\s*([^：:]+)[：:]", line)
        if not m:
            continue
        source_name = m.group(1).strip().lower()
        if source_name in TECH_SOURCE_WHITELIST:
            filtered.append(line)
    return filtered or ["今日无重大更新"]


def is_bad_discovery_title(title: str) -> bool:
    title = re.sub(r"\s+", " ", (title or "").strip())
    lower = title.lower()
    if len(title) < 12:
        return True
    if lower in {"bbc", "reuters", "ap", "guardian", "cnbc", "the verge", "techcrunch"}:
        return True
    if re.fullmatch(r"[A-Za-z .&-]+", title) and len(title.split()) <= 2:
        return True
    if title.count("|") >= 2:
        return True
    return False


def clean_summary_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if re.search(r"[\u4e00-\u9fff]", text):
        return text
    if re.search(r"[^\x00-\x7F]", text):
        return ""
    if text.count("�") >= 1:
        return ""
    if len(text) <= 20 and text.isascii() and text.isupper():
        return ""
    return text


def chineseize_text(text: str) -> str:
    text = clean_summary_text(text)
    if not text:
        return ""
    lower = text.lower()

    substring_rules = [
        (("custody", "ice"), "美国执法部门已将相关人员拘押，此举反映美伊旧案余波未散，政治象征意义大于短期军事变化。"),
        (("military approval", "abroad"), "德国相关法规显示欧洲安全压力仍在上升，人员长期出境可能被纳入更严格的国防与预备役管理框架。"),
        (("epstein", "gates"), "盖茨与爱泼斯坦旧关系再被放大，已影响慈善捐赠与精英圈互动，对市场层面影响有限但舆论冲击明显。"),
        (("service member", "iran"), "伊朗相关救援任务引发市场化押注争议，反映中东局势已外溢到美国国内政治与舆论层面。"),
        (("ukraine",), "俄乌局势仍处拉锯状态，欧洲安全外溢风险未消，但若缺乏新增官方口径，不宜过度延展解读。"),
        (("china", "hong kong"), "中方围绕涉港规则调整向美方提出抗议，显示中美在政治与制度议题上的摩擦仍未降温。"),
    ]
    for keywords, zh in substring_rules:
        if all(k in lower for k in keywords):
            return zh

    regex_rules = [
        (r"\banthropic\b", "Anthropic 相关动态显示企业级大模型竞争仍在推进，重点仍是模型能力、商业化与实际部署速度。"),
        (r"\brobot(s|ics)?\b", "机器人主题热度延续，市场继续关注从演示走向真实商用落地的兑现节奏。"),
        (r"\bnvidia\b", "NVIDIA 相关动向继续牵引算力链资本开支预期，是当前科技板块的重要风向标。"),
        (r"\bai\b", "AI 赛道仍是科技主线之一，重点在真实付费场景、企业采用进度与算力投入是否持续。"),
    ]
    for pattern, zh in regex_rules:
        if re.search(pattern, lower):
            return zh
    return text


def compress_to_30_zh(text: str) -> str:
    text = clean_summary_text(text)
    if not text:
        return "今日无额外摘要。"
    if re.search(r"[A-Za-z]", text):
        text = chineseize_text(text)
    text = re.sub(r"[。！？]+", "。", text)
    text = re.sub(r"[，,；;：:]$", "", text)
    if len(text) <= 36:
        return text if text.endswith("。") else text + "。"
    cut = text[:34].rstrip("，,；;：: ")
    if len(cut) >= 2 and cut[-1] in {"投", "牵", "推", "升", "落", "配", "需", "看", "处", "受", "走"}:
        cut = cut[:-1]
    if len(cut) < 8:
        return "今日无额外摘要。"
    return cut + "。"


def title_to_cn(title: str) -> str | None:
    raw = clean_summary_text(title)
    lower = raw.lower()
    mappings = [
        (("soleimani", "arrested"), "美国拘押苏莱曼尼亲属事件升温"),
        (("military approval", "abroad"), "德国收紧适龄男性长期出境管理"),
        (("ukraine",), "俄乌相关局势仍在发酵"),
        (("gaza",), "加沙局势仍牵动中东风险定价"),
        (("oil", "brent"), "国际油价与布伦特走势继续受关注"),
        (("epstein", "gates"), "盖茨与爱泼斯坦旧关系再掀风波"),
        (("service member", "iran"), "伊朗相关救援押注引发美国舆论争议"),
        (("hong kong",), "中方就涉港规则变动再向美方交涉"),
        (("anthropic",), "Anthropic 动向仍值得跟踪"),
        (("nvidia",), "NVIDIA 相关动向继续影响算力板块"),
        (("robot",), "机器人与自动化主题继续升温"),
        (("ai",), "AI 产业动态持续推升科技关注度"),
        (("artemis",), "航天任务动态带动科技与国防关注度"),
    ]
    for keywords, zh in mappings:
        if all(k in lower for k in keywords):
            return zh
    return None


def is_query_like_title(title: str) -> bool:
    raw = clean_summary_text(title)
    lower = raw.lower()
    if not raw:
        return True
    if lower.startswith(("site:", "intitle:", "inurl:", "filetype:")):
        return True
    query_markers = [
        " latest news",
        " breaking news",
        " top news",
        " search",
        "site:",
        "intitle:",
        "inurl:",
        "filetype:",
    ]
    if any(marker in lower for marker in query_markers):
        return True
    if re.fullmatch(r"[a-z0-9:\-./?=&_ ]+", lower) and len(raw.split()) <= 12:
        return True
    return False


def summary_is_weak(summary: str) -> bool:
    text = clean_summary_text(summary)
    if not text:
        return True
    weak_markers = {
        "今日无额外摘要。",
        "今日无额外摘要",
        "需继续跟踪后续更新。",
        "需继续跟踪后续更新",
        "今日仅抓到标题级线索，建议继续复核正文。",
    }
    if text in weak_markers:
        return True
    return len(text) < 10


def localize_headline(title: str, summary: str) -> tuple[str | None, str | None]:
    raw = f"{title} {summary}".lower()
    rules = [
        (("kharg island", "iran"), "美国关注伊朗哈尔格岛能源枢纽风险", "若伊朗关键原油出口设施受威胁，全球油价与地缘风险溢价仍可能继续上行。"),
        (("oil tanker", "cuba"), "俄油轮抵达古巴，能源与制裁博弈升温", "俄美在能源运输与地区影响力上的互动仍会扰动市场对能源供应和制裁执行的预期。"),
        (("oil prices rise", "brent"), "油价继续上行，布伦特月度涨势扩大", "中东局势持续推升风险溢价，原油价格仍处高波动区间。"),
        (("iran", "water", "power"), "中东冲突开始冲击水电等民生基础设施", "冲突外溢至民生与工业设施，说明局势对经济层面的冲击正在加深。"),
        (("houthi", "missiles"), "也门方向袭扰升级，红海与中东航运风险再抬头", "若航运威胁持续，全球运费、保险与能源运输成本都可能继续承压。"),
        (("gaza",), "加沙局势仍牵动中东风险定价", "加沙若出现新一轮军事或人道事件，市场会迅速重估中东冲突外溢风险。"),
        (("russia", "ukraine"), "俄乌相关局势仍在发酵", "欧洲安全与外交层面的外溢风险仍在，但若缺少更扎实新增口径，不展开过度演绎。"),
        (("china", "trade"), "中美经贸摩擦仍有新动向", "若涉及调查、限制或官方表态升级，市场会重新评估供应链与风险偏好。"),
        (("tariff", "trump"), "美国关税口径再起波动", "若涉及新一轮关税或经贸表态，全球风险偏好与出口链预期都会受到影响。"),
        (("stocks", "market"), "全球市场仍在围绕风险偏好重新定价", "若市场报道聚焦波动与风险偏好，说明资金仍在等待更明确的宏观与地缘信号。"),
        (("openai", "gpt"), "OpenAI 相关动态继续牵动科技板块预期", "大模型产品、商业化与监管进展仍是科技资产定价的重要变量。"),
        (("anthropic",), "Anthropic 继续推动企业级 AI 竞争", "企业端模型能力与商业化落地仍是当前 AI 板块的重要观察点。"),
        (("nvidia",), "NVIDIA 相关动向继续影响算力板块", "算力资本开支与芯片供需预期仍直接影响科技股风险偏好。"),
        (("tesla", "robot"), "机器人主题继续升温", "若头条直接涉及机器人或自动化，说明资金仍在追逐 AI 向硬件落地的延伸故事。"),
        (("artemis",), "航天任务动态带动科技与国防关注度", "载人登月与航天任务推进，通常会带动航天科技、国防工业与高端制造关注度。"),
    ]
    for keywords, zh_title, zh_summary in rules:
        if all(k in raw for k in keywords):
            return zh_title, compress_to_30_zh(zh_summary)
    title_clean = re.sub(r"\s+", " ", title).strip()
    if is_bad_discovery_title(title_clean):
        return None, None
    forced_cn = title_to_cn(title_clean)
    if forced_cn:
        safe_summary = summary or title_clean
        if re.search(r"[^\x00-\x7F]", safe_summary) and not re.search(r"[\u4e00-\u9fff]", safe_summary):
            safe_summary = title_clean
        return forced_cn, compress_to_30_zh(safe_summary)
    if re.search(r"[A-Za-z]", title_clean):
        return title_clean, compress_to_30_zh(summary or title_clean)
    return title_clean, compress_to_30_zh(summary or "今日无额外摘要。")


def news_priority_score(item: dict[str, str]) -> int:
    text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('source', '')}".lower()
    score = 0
    priority_rules = [
        (("gaza",), 120),
        (("iran",), 110),
        (("israel",), 105),
        (("middle east",), 100),
        (("ukraine",), 95),
        (("russia",), 90),
        (("china", "trade"), 88),
        (("tariff",), 85),
        (("market",), 80),
        (("stocks",), 78),
        (("oil",), 76),
        (("brent",), 75),
        (("gold",), 72),
        (("ai",), 40),
        (("anthropic",), 38),
        (("nvidia",), 36),
        (("artemis",), 20),
        (("moon",), 18),
    ]
    for keywords, pts in priority_rules:
        if all(k in text for k in keywords):
            score = max(score, pts)
    source = (item.get("source") or "").lower()
    if "reuters" in source:
        score += 40
    elif source.startswith("ap") or "ap news" in source:
        score += 32
    elif "al jazeera" in source:
        score += 28
    elif "bbc" in source:
        score += 18
    elif "cnbc" in source:
        score += 6
    return score


def classify_headline_tier(item: dict[str, str]) -> int:
    text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('source', '')}".lower()
    source = (item.get("source") or "").lower()
    tier1_keywords = [
        "gaza", "israel", "iran", "middle east", "ukraine", "russia",
        "china trade", "us-china", "tariff", "sanction", "shipping",
        "oil", "brent", "energy", "war", "conflict", "ceasefire",
    ]
    if any(keyword in text for keyword in tier1_keywords):
        return 1
    if any(name in source for name in ["reuters", "ap news", "associated press", "al jazeera"]):
        return 1
    if "bbc" in source and any(keyword in text for keyword in ["world", "iran", "gaza", "ukraine", "russia", "china", "trade", "war", "conflict"]):
        return 1
    return 2


def news_items_to_pairs(items: Iterable[dict[str, str]], require_evidence: bool = True) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen_display_titles: set[str] = set()
    all_items = sorted(list(items), key=news_priority_score, reverse=True)
    sorted_items = [item for item in all_items if classify_headline_tier(item) == 1] + [item for item in all_items if classify_headline_tier(item) != 1]
    for item in sorted_items:
        title = item.get("title", "").strip()
        summary = re.sub(r"<[^>]+>", "", item.get("summary", "")).strip()
        if not title or is_stale(title) or is_query_like_title(title):
            continue
        if require_evidence and not item.get("has_evidence"):
            continue
        zh_title, zh_summary = localize_headline(title, summary)
        if not zh_title or is_query_like_title(zh_title):
            continue
        if zh_summary and re.search(r"[^\x00-\x7F]", zh_summary) and not re.search(r"[\u4e00-\u9fff]", zh_summary):
            zh_summary = "今日无额外摘要。"
        if summary_is_weak(zh_summary):
            fallback_summary = compress_to_30_zh(summary or title)
            if not summary_is_weak(fallback_summary):
                zh_summary = fallback_summary
        if summary_is_weak(zh_summary):
            continue
        pub_date = item.get("pub_date") or "未知"
        if str(pub_date).startswith("搜索发现"):
            pub_date = "已抓正文，精确时间待补" if item.get("has_evidence") else "来源站点已命中，发布时间待补"
        display_title = f"{zh_title}（来源：{item.get('source', '未知')} | 发布时间：{pub_date}）"
        display_key = zh_title.strip().lower()
        if display_key in seen_display_titles:
            continue
        seen_display_titles.add(display_key)
        pairs.append((display_title, zh_summary or "今日无额外摘要。"))
    return pairs


def fallback_news_items_to_pairs(items: Iterable[dict[str, str]], require_evidence: bool = True) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen_titles: set[str] = set()
    sorted_items = sorted(list(items), key=news_priority_score, reverse=True)
    for item in sorted_items:
        title = re.sub(r"\s+", " ", (item.get("title") or "").strip())
        summary = re.sub(r"<[^>]+>", "", (item.get("summary") or "").strip())
        preview = re.sub(r"<[^>]+>", "", (item.get("evidence_preview") or "").strip())
        source = (item.get("source") or "未知").strip()
        pub_date = (item.get("pub_date") or "未知").strip()
        if not title or is_stale(title) or is_query_like_title(title):
            continue
        if require_evidence and not item.get("has_evidence"):
            continue
        key = title.lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        display_title = f"{title}（来源：{source} | 发布时间：{pub_date}）"
        display_summary = summary or preview or title
        display_summary = re.sub(r"\s+", " ", display_summary).strip()
        if len(display_summary) > 120:
            display_summary = display_summary[:120].rstrip(" ,;，；。") + "…"
        if not display_summary:
            display_summary = "正文已抓取，但当前缺少可用摘要。"
        pairs.append((display_title, display_summary))
    return pairs


def format_commodity_line(name: str, last_value: str, open_value: str, range_value: str) -> str:
    if last_value != "今日无重大更新":
        details: list[str] = []
        if open_value != "今日无重大更新":
            details.append(f"Open {open_value}")
        if range_value != "今日无重大更新":
            details.append(f"Range {range_value}")
        if details:
            return f"- {name}：{last_value}（{' | '.join(details)}）"
        return f"- {name}：{last_value}"
    if range_value != "今日无重大更新":
        return f"- {name}：今日无重大更新（仅抓到区间 {range_value}）"
    return f"- {name}：今日无重大更新"


def build_report() -> tuple[str, str, str]:
    now = dt.datetime.now()
    title_date = now.strftime("%Y-%m-%d")
    sent_at = now.strftime("%Y-%m-%d %H:%M:%S")
    rss_items = fetch_rss_items(limit_per_feed=3, min_age_hours=FRESH_MIN_HOURS, max_age_hours=FRESH_MAX_HOURS)
    search_items = discover_news_via_multi_search()
    merged_news = dedupe_news_items(rss_items + search_items)
    enriched_news, evidence_stats = enrich_news_items_with_evidence(merged_news)
    market = collect_market_snapshot()
    commodities = collect_commodity_snapshot()
    geo = collect_geopolitical_snapshot()
    tech = collect_tech_snapshot()

    subject = f"全球综合情报报告 - {title_date}"
    core_summary_pairs = news_items_to_pairs(enriched_news)[:5]
    if not core_summary_pairs and merged_news:
        core_summary_pairs = news_items_to_pairs(enriched_news, require_evidence=False)[:5]
    if not core_summary_pairs:
        core_summary_pairs = fallback_news_items_to_pairs(enriched_news)[:5]
    if not core_summary_pairs:
        core_summary_pairs = fallback_news_items_to_pairs(enriched_news, require_evidence=False)[:5]
    if not core_summary_pairs:
        core_summary_pairs = [("今日无足够扎实头条更新", "本轮自动抓取与搜索发现未形成足够可靠的核心头条，报告保留结构但不虚构补洞。")]

    middle_east_lines = geo["middle_east"] or ["今日无重大更新"]
    russia_ukraine_lines = geo["russia_ukraine"] or ["今日无重大更新"]
    us_china_lines = geo["us_china"] or ["今日无重大更新"]
    tech_lines = enforce_tech_source_whitelist(tech)

    lines: list[str] = [
        f"全球综合情报报告 - {title_date}",
        "",
        f"发送时间：{sent_at}",
        "整理：沈万三",
        "搜索窗口：严格限定过去24-48小时；抓不到就明确写无更新，拒绝旧闻补洞",
        "搜索增强：已接入 multi-search-engine 模板做新闻发现补充",
        f"头条准入：优先保留已抓到正文证据条目；若正文证据不足则放宽为站点命中条目并明确标注时间状态（本轮候选 {evidence_stats['inputCount']} 条，正文证据通过 {evidence_stats['withEvidence']} 条）",
        "",
        "---",
        "📊 实时头条（过去24-48小时）",
    ]

    for idx, (title_text, summary_text) in enumerate(core_summary_pairs, start=1):
        lines.append(f"{idx}. {title_text}")
        lines.append(f"   结论：{summary_text}")
        lines.append("")

    lines.extend([
        "---",
        "🌍 地缘政治分析",
        "【中东】",
    ])
    lines.extend([f"- {x}" for x in middle_east_lines])
    lines.extend([
        "",
        "【欧洲（俄乌）】",
    ])
    lines.extend([f"- {x}" for x in russia_ukraine_lines])
    lines.extend([
        "",
        "【亚太（中美/东亚）】",
    ])
    lines.extend([f"- {x}" for x in us_china_lines])
    lines.extend([
        "- 冲突核查：若同一事件存在媒体分歧，统一标注“说法不一”，并并列呈现主要口径。",
        "",
        "---",
        "📈 金融市场速报",
        "| 指数 | 点位 | 涨跌幅 |",
        "|---|---:|---:|",
        f"| S&P 500 | {market['spx']} | {market['spx_change']} |",
        f"| 上证指数 | {market.get('shanghai', '今日无重大更新')} | {market.get('shanghai_change', '今日无重大更新')} |",
        f"| 日经225 | {market['n225']} | {market['n225_change']} |",
        f"| 韩国KOSPI | {market.get('kospi', '今日无重大更新')} | {market.get('kospi_change', '今日无重大更新')} |",
        "（来源：Reuters / SSE / JPX / KRX / 东方财富 / 新浪）",
        "",
        "---",
        "⛽ 大宗商品与汇率",
        "| 资产 | 最新值 | 备注 |",
        "|---|---:|---|",
        f"| 布伦特原油 | {commodities['brent_last']} | Open {commodities['brent_open']} ; Range {commodities['brent_range']} |",
        f"| 现货黄金 | {commodities['gold_last']} | Open {commodities['gold_open']} ; Range {commodities['gold_range']} |",
        f"| 美元指数DXY | {market.get('dxy', '今日无重大更新')} | 交易所快照优先 |",
        f"| 美元兑人民币USDCNY | {market.get('usdcny', '今日无重大更新')} | 交易所快照优先 |",
        "（来源：Yahoo Finance / 交易所快照）",
        "",
        "---",
        "🧠 科技新闻版块",
        "【AI / 机器人 / 科技前沿】",
    ])
    lines.extend([f"- {x}" for x in tech_lines])
    lines.extend([
        "- 结论：科技仍是资金回流的优先方向，但估值表现仍受地缘与风险偏好支配。",
        "",
        "【美股科技龙头快照（东方财富/新浪/腾讯，如存在）】",
        f"- AAPL：{market.get('aapl', '今日无重大更新')}（{market.get('aapl_change', '变化未获取')}）",
        f"- NVDA：{market.get('nvda', '今日无重大更新')}（{market.get('nvda_change', '变化未获取')}）",
        f"- TSLA：{market.get('tsla', '今日无重大更新')}（{market.get('tsla_change', '变化未获取')}）",
        "",
        "---",
        "🚨 风险预警",
        "- 若海湾能源设施、港口、油轮继续受袭，油价和运价可能再度急升。",
        "- 若也门方向或黎巴嫩战线继续升级，全球避险资产可能再次走强。",
        "- 若美股反弹缺乏后续缓和消息支撑，可能迅速回吐。",
        "- 欧洲能源与通胀压力回升将继续拖累风险资产估值。",
        "- 亚洲市场仍受汇率、外需与科技风险偏好波动牵引。",
        "",
        "---",
        "💡 决策建议",
        "- 当前更适合防守型 + 事件驱动型交易，不是舒服做多的环境。",
        "- 黄金与能源仍有配置价值，但波动极高，需严格控制仓位与节奏。",
        "- 科技与电子链可作为回流方向观察，前提是地缘风险继续边际缓和。",
        "- 若无明确缓和信号，全球资产配置宜偏防守，优先流动性与风险对冲。",
        "",
        "说明：本报告严格限定过去24-48小时；抓不到就明确写“今日无重大更新”，不使用旧闻补洞。",
        f"报告生成时间：{sent_at} | 引用口径：Reuters / Bloomberg / WSJ / 交易所及财经页面实时抓取。",
    ])

    text_body = sanitize_report_text("\n".join(lines))

    def p(txt: str) -> str:
        return html.escape(txt)

    html_parts = [
        "<html><body style='font-family:Microsoft YaHei,Arial,sans-serif;line-height:1.75;'>",
        f"<h2>{p(subject)}</h2>",
        f"<p><b>发送时间：</b>{p(sent_at)}<br><b>整理：</b>沈万三<br><b>搜索窗口：</b>严格限定过去24-48小时；抓不到就明确写无更新，拒绝旧闻补洞<br><b>搜索增强：</b>已接入 multi-search-engine 模板做新闻发现补充</p>",
    ]
    for line in text_body.splitlines()[7:]:
        if line == "---":
            html_parts.append("<hr>")
        elif re.match(r"^[一二三四五六七八九十]+、", line) or line.startswith(("📊", "🌍", "📈", "⛽", "🚨", "💡", "🧠")):
            html_parts.append(f"<h3>{p(line)}</h3>")
        elif line.startswith("【") and line.endswith("】"):
            html_parts.append(f"<h4>{p(line)}</h4>")
        elif re.match(r"^\d+\. ", line):
            html_parts.append(f"<p><b>{p(line)}</b></p>")
        elif line.startswith("- "):
            html_parts.append(f"<p>{p(line)}</p>")
        elif line.startswith("结论：") or line.startswith("说明：") or line.startswith("（来源：") or line.startswith("   结论："):
            html_parts.append(f"<p>{p(line)}</p>")
        elif line.strip() == "":
            html_parts.append("<br>")
        else:
            html_parts.append(f"<p>{p(line)}</p>")
    html_parts.append("</body></html>")
    html_body = sanitize_report_text("\n".join(html_parts))
    return subject, text_body, html_body


def send_email(subject: str, text_body: str, html_body: str) -> None:
    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECEIVERS)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(text_body, subtype="plain", charset="utf-8")
    msg.add_alternative(html_body, subtype="html", charset="utf-8")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=TIMEOUT_SECONDS) as smtp:
        smtp.login(SENDER, AUTH_CODE)
        smtp.send_message(msg)


if __name__ == "__main__":
    subject, text_body, html_body = build_report()
    print("SUBJECT:", subject)
    print("TEXT_PREVIEW_START")
    print(text_body[:5000])
    print("TEXT_PREVIEW_END")
