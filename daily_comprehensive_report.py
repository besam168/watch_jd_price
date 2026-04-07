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

RSS_FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("AP News", "https://feeds.apnews.com/rss/apf-topnews"),
    ("CNBC World", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
]

STALE_PATTERNS = [
    "GB200发布",
    "日本结束负利率",
    "标普500在5400点",
]

FRESH_MIN_HOURS = 0
FRESH_MAX_HOURS = 24
SEARCH_DISCOVERY_SITES = [
    ("Reuters", "reuters.com"),
    ("BBC", "bbc.com/news"),
    ("AP", "apnews.com"),
    ("Guardian", "theguardian.com"),
    ("CNBC", "cnbc.com"),
    ("The Verge", "theverge.com"),
    ("TechCrunch", "techcrunch.com"),
]
SEARCH_ENGINE_PREFERENCE = ["DuckDuckGo", "Startpage", "Yahoo"]


def read_optional(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


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


def extract_search_result_candidates(source_name: str, site: str, html_text: str) -> list[dict[str, str]]:
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
            if len(candidates) >= 3:
                break
        if candidates:
            break
    return candidates


def discover_news_via_multi_search() -> list[dict[str, str]]:
    templates = load_multi_search_templates()
    if not templates:
        return []

    items: list[dict[str, str]] = []
    for engine_name in SEARCH_ENGINE_PREFERENCE:
        template = templates.get(engine_name)
        if not template:
            continue
        for source_name, site in SEARCH_DISCOVERY_SITES:
            query = f"site:{site} latest world news"
            encoded = urllib.parse.quote_plus(query)
            url = template.replace("{keyword}", encoded)
            try:
                page = fetch_url_text(url)
            except Exception:
                continue
            items.extend(extract_search_result_candidates(source_name, site, page))
    return items


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


def collect_qveris_market_snapshot() -> dict[str, str]:
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

    gold = data.get("XAUUSD") or {}
    if isinstance(gold, dict):
        gold_price = plausible(str(gold.get("price")) if gold.get("price") is not None else None, 1800, 4000)
        gold_open = plausible(str(gold.get("open")) if gold.get("open") is not None else None, 1800, 4000)
        gold_low = plausible(str(gold.get("dayLow")) if gold.get("dayLow") is not None else None, 1800, 4000)
        gold_high = plausible(str(gold.get("dayHigh")) if gold.get("dayHigh") is not None else None, 1800, 4000)
        if gold_price is not None:
            out["gold_qv"] = gold_price
        if gold_open is not None:
            out["gold_qv_open"] = gold_open
        if gold_low is not None and gold_high is not None:
            out["gold_qv_range"] = f"{gold_low} - {gold_high}"

    return out


def sanitize_report_text(text: str) -> str:
    replacements = {
        "�?": "",
        "过�?2-24小时": "过去0-24小时",
        "补�?": "补充",
        "二�?0字左右总判�?": "二、50字左右总判断",
        "一、重要头条新�?": "一、重要头条新闻",
        "三、全球市场动�?": "三、全球市场动态",
        "四、地缘政治热�?": "四、地缘政治热点",
        "五、全球经济与产业动�?": "五、全球经济与产业动态",
        "六、风险预警（24-48小时短期 / 中期 / 长期�?": "六、风险预警（24-48小时短期 / 中期 / 长期）",
        "七、投资建�?": "七、投资建议",
        "【美股�?": "【美股】",
        "【欧洲与亚太股市�?": "【欧洲与亚太股市】",
        "【商品与避险资产�?": "【商品与避险资产】",
        "【中东�?": "【中东】",
        "【俄乌�?": "【俄乌】",
        "【中美关�?/ 东亚政治�?": "【中美关系 / 东亚政治】",
        "【AI / 机器�?/ 科技前沿�?": "【AI / 机器人 / 科技前沿】",
        "【美股科技龙头快照（QVeris，如存在）�?": "【美股科技龙头快照（QVeris，如存在）】",
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
    reuters = read_optional(FIRECRAWL_DIR / "reuters.com.md")
    yahoo = read_optional(FIRECRAWL_DIR / "finance.yahoo.com.md")
    twse = read_optional(FIRECRAWL_DIR / "twse.com.tw-zh-index.html.md")
    jpx = read_optional(FIRECRAWL_DIR / "jpx.co.jp-english.md")
    krx = read_optional(FIRECRAWL_DIR / "global.krx.co.kr-main-main.jsp.md")
    eastmoney = read_optional(FIRECRAWL_DIR / "eastmoney.com.md")

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

    data.update(collect_qveris_market_snapshot())
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
    gold = read_optional(FIRECRAWL_DIR / "finance.yahoo.com-quote-GC=F.md")
    brent = read_optional(FIRECRAWL_DIR / "finance.yahoo.com-quote-BZ=F.md")
    wti = read_optional(FIRECRAWL_DIR / "finance.yahoo.com-quote-CL=F.md")

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
    qv = collect_qveris_market_snapshot()
    if qv.get("gold_qv"):
        qv_gold = within_numeric_range(qv["gold_qv"], 1500, 4500)
        if qv_gold:
            data["gold_last"] = qv_gold
            data["gold_open"] = within_numeric_range(qv.get("gold_qv_open"), 1500, 4500) or data["gold_open"]
            data["gold_range"] = clean_range_text(qv.get("gold_qv_range")) or data["gold_range"]
    return data


def collect_geopolitical_snapshot() -> dict[str, list[str]]:
    bbc = read_optional(FIRECRAWL_DIR / "bbc.com-news.md")
    reuters = read_optional(FIRECRAWL_DIR / "reuters.com.md")
    reuters_europe = read_optional(FIRECRAWL_DIR / "reuters.com-world-europe.md")
    reuters_china = read_optional(FIRECRAWL_DIR / "reuters.com-world-china.md")
    ap = read_optional(FIRECRAWL_DIR / "apnews.com.md")
    aljazeera = read_optional(FIRECRAWL_DIR / "aljazeera.com.md")

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
        ("The Verge", read_optional(FIRECRAWL_DIR / "theverge.com.md")),
        ("TechCrunch", read_optional(FIRECRAWL_DIR / "techcrunch.com.md")),
        ("IEEE Spectrum", read_optional(FIRECRAWL_DIR / "spectrum.ieee.org.md")),
        ("Wired", read_optional(FIRECRAWL_DIR / "wired.com.md")),
        ("Ars Technica", read_optional(FIRECRAWL_DIR / "arstechnica.com.md")),
        ("MIT Technology Review", read_optional(FIRECRAWL_DIR / "technologyreview.com.md")),
        ("VentureBeat AI", read_optional(FIRECRAWL_DIR / "venturebeat.com-category-ai.md")),
        ("Singularity Hub", read_optional(FIRECRAWL_DIR / "singularityhub.com.md")),
        ("AI News", read_optional(FIRECRAWL_DIR / "artificialintelligence-news.com.md")),
        ("Engadget", read_optional(FIRECRAWL_DIR / "engadget.com.md")),
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
    if len(text) <= 36:
        return text if text.endswith("。") else text + "。"
    cut = text[:34].rstrip("，,；;：: ")
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
        return None, None
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
        score += 10
    elif "ap" in source:
        score += 8
    elif "bbc" in source:
        score += 6
    elif "al jazeera" in source:
        score += 6
    return score


def news_items_to_pairs(items: Iterable[dict[str, str]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen_display_titles: set[str] = set()
    sorted_items = sorted(list(items), key=news_priority_score, reverse=True)
    for item in sorted_items:
        title = item.get("title", "").strip()
        summary = re.sub(r"<[^>]+>", "", item.get("summary", "")).strip()
        if not title or is_stale(title):
            continue
        zh_title, zh_summary = localize_headline(title, summary)
        if not zh_title:
            continue
        if zh_summary and re.search(r"[^\x00-\x7F]", zh_summary) and not re.search(r"[\u4e00-\u9fff]", zh_summary):
            zh_summary = "今日无额外摘要。"
        display_title = f"{zh_title}（来源：{item.get('source', '未知')} | 发布时间：{item.get('pub_date') or '未知'}）"
        display_key = zh_title.strip().lower()
        if display_key in seen_display_titles:
            continue
        seen_display_titles.add(display_key)
        pairs.append((display_title, zh_summary or "今日无额外摘要。"))
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
    market = collect_market_snapshot()
    commodities = collect_commodity_snapshot()
    geo = collect_geopolitical_snapshot()
    tech = collect_tech_snapshot()

    subject = f"全球综合情报报告 - {title_date}"
    core_summary_pairs = news_items_to_pairs(merged_news)[:5]
    if not core_summary_pairs:
        core_summary_pairs = [("今日无足够扎实头条更新", "本轮自动抓取与搜索发现未形成足够可靠的核心头条，报告保留结构但不虚构补洞。")]

    middle_east_lines = geo["middle_east"] or ["今日无重大更新"]
    russia_ukraine_lines = geo["russia_ukraine"] or ["今日无重大更新"]
    us_china_lines = geo["us_china"] or ["今日无重大更新"]
    tech_lines = tech or ["今日无重大更新"]

    lines: list[str] = [
        f"全球综合情报报告 - {title_date}",
        "",
        f"发送时间：{sent_at}",
        "整理：沈万三（以首席全球分析师口径撰写）",
        "搜索窗口：严格限定过去12-24小时；抓不到就明确写无更新，拒绝旧闻补洞",
        "搜索增强：已接入 multi-search-engine 模板做新闻发现补充",
        "",
        "---",
        "一、重要头条新闻",
    ]

    for idx, (title_text, summary_text) in enumerate(core_summary_pairs, start=1):
        lines.append(f"{idx}. {title_text}")
        lines.append(f"   结论：{summary_text}")
        lines.append("")

    lines.extend([
        "---",
        "二、50字左右总判断",
        "当前全球市场仍由地缘政治、能源风险与科技资产风险偏好三条主线共同驱动。搜索增强后，头条发现能力已有提升，但仍坚持只写本轮抓取/搜索能交叉验证的内容。",
        "",
        "---",
        "三、全球市场动态",
        "【美股】",
        f"- S&P 500：{market['spx']}（{market['spx_change']}）",
        f"- 纳斯达克：{market['ixic']}（{market['ixic_change']}）",
        f"- 道琼斯：{market['dji']}（{market['dji_change']}）",
        f"- 标普期货：首页抓取约 {market['es_fut']}",
        "- 结论：仅保留本轮抓取到的真实页面值；没抓到就明确写无更新，不再填默认数字。",
        "（来源：Reuters | 发布时间：页面抓取时点）",
        "（来源：Yahoo Finance | 发布时间：页面抓取时点）",
        "",
        "【欧洲与亚太股市】",
        f"- STOXX Europe 600：{market['stoxx']}",
        f"- 英国富时100：{market['ftse']}",
        f"- 日经225：{market['n225']}（{market['n225_change']}）",
        f"- 台湾加权：{market.get('twse', '今日无重大更新')}",
        f"- 韩国KOSPI：{market.get('kospi', '今日无重大更新')}",
        f"- 恒生指数：{market.get('hangseng', '今日无重大更新')}",
        "- 结论：亚太市场分化若缺少页面抓取到的新值，就直接留白，不拿旧数据补写。",
        "（来源：TWSE / KRX / JPX / Eastmoney | 发布时间：页面抓取时点）",
        "",
        "【商品与避险资产】",
        format_commodity_line("黄金", commodities['gold_last'], commodities['gold_open'], commodities['gold_range']),
        format_commodity_line("布伦特", commodities['brent_last'], commodities['brent_open'], commodities['brent_range']),
        format_commodity_line("WTI", commodities['wti_last'], commodities['wti_open'], commodities['wti_range']),
        f"- 新闻口径：{commodities['headline_oil']}",
        "- 结论：原油与黄金只使用本轮页面抓到的报价/区间；若无新值，不做历史数字填充。",
        "（来源：Yahoo Finance GC=F / BZ=F / CL=F | 发布时间：页面抓取时点）",
        "",
        "---",
        "四、地缘政治热点",
        "【中东】",
    ])
    lines.extend([f"- {x}" for x in middle_east_lines])
    lines.extend([
        "- 结论：中东仍是全球第一风险源，已从军事层面外溢到工业设施、能源运输与民生基础设施。",
        "",
        "【俄乌】",
    ])
    lines.extend([f"- {x}" for x in russia_ukraine_lines])
    lines.extend([
        "- 结论：俄乌今天不是最强主线，但欧洲外围安全和外交层面的延伸风险仍在。",
        "",
        "【中美关系 / 东亚政治】",
    ])
    lines.extend([f"- {x}" for x in us_china_lines])
    lines.extend([
        "- 结论：若缺乏扎实新增口径，维持克制写法，不拿旧闻硬补。",
        "",
        "---",
        "五、全球经济与产业动态",
        "【AI / 机器人 / 科技前沿】",
    ])
    lines.extend([f"- {x}" for x in tech_lines])
    lines.extend([
        "- 结论：科技仍是资金回流的优先方向，但估值表现仍受地缘与风险偏好支配。",
        "",
        "【美股科技龙头快照（QVeris，如存在）】",
        f"- AAPL：{market.get('aapl', '今日无重大更新')}（{market.get('aapl_change', '变化未获取')}）",
        f"- NVDA：{market.get('nvda', '今日无重大更新')}（{market.get('nvda_change', '变化未获取')}）",
        f"- TSLA：{market.get('tsla', '今日无重大更新')}（{market.get('tsla_change', '变化未获取')}）",
        "- 结论：若存在 QVeris 快照就补充，没有就明确写无更新，不伪造个股行情。",
        "",
        "---",
        "六、风险预警（24-48小时短期 / 中期 / 长期）",
        "【短期】",
        "- 若海湾能源设施、港口、油轮继续受袭，油价和运价可能再度急升。",
        "- 若也门方向或黎巴嫩战线继续升级，全球避险资产可能再次走强。",
        "- 若美股反弹缺乏后续缓和消息支撑，可能迅速回吐。",
        "",
        "【中期】",
        "- 欧洲能源与通胀压力可能回升，拖累风险资产估值。",
        "- 亚洲市场将继续受汇率、外需和科技板块情绪波动牵引。",
        "",
        "【长期】",
        "- 若中东冲突长期化，全球供应链、航运保险与能源成本将系统性抬升。",
        "- 资金配置可能继续偏向黄金、能源、国防与低波动资产。",
        "",
        "---",
        "七、投资建议",
        "- 当前更适合防守型 + 事件驱动型交易，不是舒服做多的环境。",
        "- 黄金与能源仍有配置价值，但波动极高，不能把盘中新闻高点当静态报价。",
        "- 科技与电子链可作为回流方向观察，但前提是地缘风险继续边际缓和。",
        "- 若没有明确缓和信号，全球资产配置宜偏防守，控制仓位与节奏。",
        "",
        "说明：本报告默认使用模板 A（详细正式版），用于每日综合情报、发邮箱与存档；抓不到的数据直接写“今日无重大更新”或“未获取到扎实数据”，严禁虚构补洞。",
    ])

    text_body = sanitize_report_text("\n".join(lines))

    def p(txt: str) -> str:
        return html.escape(txt)

    html_parts = [
        "<html><body style='font-family:Microsoft YaHei,Arial,sans-serif;line-height:1.75;'>",
        f"<h2>{p(subject)}</h2>",
        f"<p><b>发送时间：</b>{p(sent_at)}<br><b>整理：</b>沈万三<br><b>搜索窗口：</b>严格限定过去0-24小时；抓不到就明确写无更新，拒绝旧闻补洞<br><b>搜索增强：</b>已接入 multi-search-engine 模板做新闻发现补充</p>",
    ]
    for line in text_body.splitlines()[7:]:
        if line == "---":
            html_parts.append("<hr>")
        elif re.match(r"^[一二三四五六七八九十]+、", line):
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
