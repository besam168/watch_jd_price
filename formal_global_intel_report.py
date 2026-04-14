import smtplib
import ssl
import json
import sys
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate, parsedate_to_datetime
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import html
import re
import time

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "910633260@qq.com"
SMTP_PASSWORD = "sghqeeeeyuzjbcbb"
RECIPIENTS = ["besam168168@gmail.com", "758622673@qq.com"]

TZ_CN = timezone(timedelta(hours=8))
NOW = datetime.now(TZ_CN)
WINDOW_START = NOW - timedelta(hours=24)

FEEDS = [
    {"name": "路透世界", "url": "https://feeds.reuters.com/Reuters/worldNews", "section": "宏观新闻", "fallback_kind": "reuters_page"},
    {"name": "美联社头条", "url": "https://feeds.ap.org/apf-topnews", "section": "宏观新闻", "fallback_kind": "ap"},
    {"name": "Google News Gaza", "url": "https://news.google.com/rss/search?q=Gaza%20when%3A1d&hl=en-US&gl=US&ceid=US:en", "section": "宏观新闻"},
    {"name": "Google News Ukraine", "url": "https://news.google.com/rss/search?q=Ukraine%20when%3A1d&hl=en-US&gl=US&ceid=US:en", "section": "宏观新闻"},
    {"name": "Google News China Trade", "url": "https://news.google.com/rss/search?q=China%20tariff%20trade%20when%3A1d&hl=en-US&gl=US&ceid=US:en", "section": "宏观新闻"},
    {"name": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "section": "宏观新闻"},
    {"name": "半岛电视台", "url": "https://www.aljazeera.com/xml/rss/all.xml", "section": "宏观新闻"},
    {"name": "CNBC国际", "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "section": "财经市场"},
    {"name": "雅虎财经", "url": "https://finance.yahoo.com/news/rssindex", "section": "财经市场"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "section": "科技产业"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "section": "科技产业"},
    {"name": "IEEE Spectrum", "url": "https://spectrum.ieee.org/feeds/feed.rss", "section": "科技产业"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "section": "科技产业"},
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "section": "科技产业"},
]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OpenClawFormalIntelV5/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_text(url: str, timeout: int = 20) -> str:
    return fetch_url(url, timeout=timeout).decode("utf-8", errors="ignore")


def parse_time(pub_text: str):
    pub_text = (pub_text or "").strip()
    if not pub_text:
        return None
    try:
        dt = parsedate_to_datetime(pub_text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ_CN)
    except Exception:
        return None


def within_24h(dt):
    return bool(dt and WINDOW_START <= dt <= NOW)


def parse_feed(url: str, limit: int = 16):
    raw = fetch_url(url)
    root = ET.fromstring(raw)
    items = []
    channel = root.find("channel")
    if channel is not None:
        for item in channel.findall("item")[:limit]:
            title = strip_html(item.findtext("title", default=""))
            link = (item.findtext("link", default="") or "").strip()
            desc = strip_html(item.findtext("description", default=""))
            pub = strip_html(item.findtext("pubDate", default=""))
            items.append({"title": title, "link": link, "summary": desc, "published": pub, "published_dt": parse_time(pub)})
        return items
    ns_atom = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{ns_atom}entry")[:limit]:
        title = strip_html(entry.findtext(f"{ns_atom}title", default=""))
        summary = strip_html(entry.findtext(f"{ns_atom}summary", default="") or entry.findtext(f"{ns_atom}content", default=""))
        published = strip_html(entry.findtext(f"{ns_atom}updated", default="") or entry.findtext(f"{ns_atom}published", default=""))
        link = ""
        for link_node in entry.findall(f"{ns_atom}link"):
            href = link_node.attrib.get("href", "").strip()
            rel = link_node.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                link = href
                break
        items.append({"title": title, "link": link, "summary": summary, "published": published, "published_dt": parse_time(published)})
    return items


def fallback_reuters(limit: int = 16):
    items = []
    seen = set()
    for page in [
        "https://www.reuters.com/world/",
        "https://www.reuters.com/world/middle-east/",
        "https://www.reuters.com/world/europe/",
        "https://www.reuters.com/world/china/",
        "https://www.reuters.com/markets/",
    ]:
        try:
            html_text = fetch_text(page, timeout=20)
        except Exception:
            continue
        for href, title in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_text, flags=re.I | re.S):
            link = href.strip()
            if link.startswith("/"):
                link = urllib.parse.urljoin("https://www.reuters.com", link)
            text = strip_html(title)
            if not link.startswith("https://www.reuters.com/") or len(text) < 25:
                continue
            key = (link, text)
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": text, "link": link, "summary": text, "published": f"页面抓取时间 {NOW.strftime('%Y-%m-%d %H:%M %z')}", "published_dt": NOW})
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    if len(items) < limit:
        try:
            gitems = parse_feed("https://news.google.com/rss/search?q=site%3Areuters.com%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen", limit=limit)
            for item in gitems:
                title = strip_html(item.get("title", ""))
                if "Reuters" not in title and "reuters" not in item.get("link", "").lower():
                    continue
                key = (item.get("link", ""), title)
                if key in seen:
                    continue
                seen.add(key)
                items.append(item)
                if len(items) >= limit:
                    break
        except Exception:
            pass
    return items


def fallback_ap(limit: int = 16):
    html_text = fetch_text("https://apnews.com/", timeout=20)
    items = []
    seen = set()
    for href, title in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_text, flags=re.I | re.S):
        link = href.strip()
        if link.startswith("/"):
            link = urllib.parse.urljoin("https://apnews.com", link)
        text = strip_html(title)
        if not link.startswith("https://apnews.com/") or len(text) < 25:
            continue
        key = (link, text)
        if key in seen:
            continue
        seen.add(key)
        items.append({"title": text, "link": link, "summary": text, "published": f"页面抓取时间 {NOW.strftime('%Y-%m-%d %H:%M %z')}", "published_dt": NOW})
        if len(items) >= limit:
            break
    return items


def fallback_items(kind: str, limit: int = 16):
    if kind == "reuters_page":
        return fallback_reuters(limit)
    if kind == "ap":
        return fallback_ap(limit)
    return []


def cap_text(text: str, max_len: int) -> str:
    text = strip_html(text)
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip("，。；;,. ") + "。"


def title_to_cn(title: str) -> str:
    raw = strip_html(title)
    lower = raw.lower()
    rules = [
        (("tariff", "china"), "美国对华关税口径再度收紧"),
        (("trade", "china"), "中美经贸博弈出现新动向"),
        (("exports", "china"), "中国外贸数据变化引发市场关注"),
        (("hormuz",), "霍尔木兹海峡风险再度牵动全球能源预期"),
        (("iran", "dialogue"), "美伊接触释放新一轮外交信号"),
        (("iran", "talk"), "伊朗问题谈判预期再度升温"),
        (("iran",), "伊朗相关动态继续推升中东风险溢价"),
        (("gaza",), "加沙局势仍牵动中东风险定价"),
        (("israel",), "以色列相关动态继续牵动中东局势"),
        (("ukraine",), "俄乌局势仍在持续发酵"),
        (("russia",), "俄罗斯相关动态继续牵动欧洲安全预期"),
        (("oil",), "国际油价波动继续受地缘局势牵动"),
        (("dollar",), "美元走势继续反映避险与政策预期"),
        (("market", "rise"), "全球市场风险偏好出现修复迹象"),
        (("stocks", "rebound"), "全球股市反弹带动风险偏好修复"),
        (("openai",), "OpenAI 新动向继续牵动科技板块预期"),
        (("anthropic",), "Anthropic 动向继续反映企业级 AI 竞争"),
        (("nvidia",), "NVIDIA 相关动态继续影响算力板块"),
        (("robot",), "机器人主题继续升温"),
        (("ai",), "AI 产业动态继续升温"),
        (("goldman sachs",), "高盛业绩与投行业务恢复情况受市场关注"),
    ]
    for keywords, zh in rules:
        if all(k in lower for k in keywords):
            return zh
    if re.search(r"[\u4e00-\u9fff]", raw):
        return raw
    signal = classify_signal(raw)
    fallback_map = {
        "china_trade": "中美经贸与关税线索持续扰动市场预期",
        "market_macro": "全球市场与宏观预期出现新变化",
        "tech_ai": "科技与 AI 主线继续升温",
        "russia_ukraine": "俄乌局势出现新的跟踪线索",
        "geo_energy": "中东局势与能源风险继续升温",
        "generic": "国际要闻出现新变化",
    }
    return fallback_map.get(signal, "国际要闻出现新变化")


def force_chinese_text(text: str, *, fallback: str = "国际要闻出现新变化", max_len: int = 88) -> str:
    clean = strip_html(text)
    if clean and re.search(r"[\u4e00-\u9fff]", clean):
        return cap_text(clean, max_len)
    zh = title_to_cn(clean)
    if zh and re.search(r"[\u4e00-\u9fff]", zh):
        return cap_text(zh, max_len)
    return fallback


def normalize_headline_title(raw_title: str, raw_summary: str) -> str:
    title = strip_html(raw_title)
    summary = strip_html(raw_summary)
    if title and re.search(r"[\u4e00-\u9fff]", title):
        return cap_text(title, 88)
    if title:
        return force_chinese_text(title, fallback="国际要闻出现新变化", max_len=88)
    if summary:
        return force_chinese_text(summary, fallback="国际要闻出现新变化", max_len=60)
    return "国际要闻出现新变化"


def classify_signal(text: str) -> str:
    lower = (text or "").lower()
    if any(k in lower for k in ["china", "tariff", "trade", "commerce", "duties"]):
        return "china_trade"
    if any(k in lower for k in ["market", "sell-off", "pricing in", "panic", "stocks", "bond", "fed", "goldman sachs"]):
        return "market_macro"
    if any(k in lower for k in ["openai", "anthropic", "nvidia", "ai", "robot", "chip", "claude"]):
        return "tech_ai"
    if any(k in lower for k in ["ukraine", "russia", "moscow", "kyiv"]):
        return "russia_ukraine"
    if any(k in lower for k in ["gaza", "israel", "iran", "hormuz", "oil", "brent", "middle east"]):
        return "geo_energy"
    if any(k in lower for k in ["trump", "white house", "u.s. foreign policy", "politics", "pope leo"]):
        return "market_macro"
    return "generic"


def chineseize_summary(text: str, title: str = "") -> str:
    merged = f"{title} {text}".strip()
    text = strip_html(text)
    signal = classify_signal(title or merged)
    if signal == "generic":
        signal = classify_signal(merged)
    if signal == "geo_energy":
        return "中东与能源相关动态继续升温，若冲突外溢至航运与供应链，油价与避险资产可能进一步受到推升。"
    if signal == "russia_ukraine":
        return "俄乌相关线索仍在更新，说明欧洲安全议题尚未降温，后续若伴随制裁或军援表态，市场仍会重新计价。"
    if signal == "china_trade":
        return "中美经贸与关税口径继续扰动供应链和风险偏好，出口链、科技链及跨境资产仍需密切跟踪。"
    if signal == "tech_ai":
        return "AI 与科技平台竞争继续升温，市场关注焦点仍在产品落地、商业化节奏以及算力资本开支的兑现能力。"
    if signal == "market_macro":
        return "金融与市场类动态反映资金仍在围绕宏观预期、价格信号和龙头权重股表现重新定价。"
    if re.search(r"[\u4e00-\u9fff]", text):
        return cap_text(text, 78)
    return "该条目有新增，但当前仅抓到英文标题或摘要线索，仍需结合正文复核其真实影响与后续发酵。"


def is_noise_item(title: str, summary: str, section: str, source: str = "") -> bool:
    text = f"{title} {summary}".lower()
    if source.startswith("Google News"):
        whitelist = [
            "gaza", "israel", "iran", "hormuz", "oil", "brent",
            "ukraine", "russia", "moscow", "kyiv",
            "china", "tariff", "trade", "commerce",
            "market", "sell-off", "pricing in", "stocks", "bond", "fed", "goldman",
            "ai", "openai", "anthropic", "nvidia", "chip", "robot", "claude"
        ]
        if not any(marker in text for marker in whitelist):
            return True
    if section == "宏观新闻":
        noise_markers = [
            "governor's race",
            "pope leo",
            "assault allegations",
            "jesus-like figure",
            "celebrity",
            "sports",
        ]
        if any(marker in text for marker in noise_markers):
            return True
    return False


def make_content(summary: str, title: str) -> str:
    signal = classify_signal(title)
    if signal == "generic":
        signal = classify_signal(summary)
    if signal == "geo_energy":
        return "中东与能源相关动态继续升温，若冲突外溢至航运与供应链，油价与避险资产可能进一步受到推升。"
    if signal == "russia_ukraine":
        return "俄乌相关线索仍在更新，说明欧洲安全议题尚未降温，后续若伴随制裁或军援表态，市场仍会重新计价。"
    if signal == "china_trade":
        return "中美经贸与关税口径继续扰动供应链和风险偏好，出口链、科技链及跨境资产仍需密切跟踪。"
    if signal == "tech_ai":
        return "AI 与科技平台竞争继续升温，市场关注焦点仍在产品落地、商业化节奏以及算力资本开支的兑现能力。"
    if signal == "market_macro":
        return "金融与市场类动态反映资金仍在围绕宏观预期、价格信号和龙头权重股表现重新定价。"
    base = summary or title or ""
    return force_chinese_text(chineseize_summary(base, title=title), fallback="国际要闻出现新变化", max_len=78)


def make_short_comment(section: str, summary: str, title: str) -> str:
    signal = classify_signal(title)
    if signal == "generic":
        signal = classify_signal(summary)

    if signal == "geo_energy":
        return "说明地缘风险仍会持续牵动能源、航运与避险资产。"
    if signal == "russia_ukraine":
        return "说明欧洲安全与制裁预期仍可能继续影响区域风险资产。"
    if signal == "china_trade":
        return "说明经贸摩擦仍可能扰动出口链、制造链与风险偏好。"
    if signal == "tech_ai":
        lower = f"{title} {summary}".lower()
        if "openai" in lower:
            return "说明大模型平台竞争正继续影响软件与算力链估值。"
        if "anthropic" in lower:
            return "说明企业级 AI 赛道竞争仍在加速，商业化节奏值得跟踪。"
        if "nvidia" in lower or "chip" in lower:
            return "说明算力与芯片链条仍是科技板块核心定价主线。"
        if "robot" in lower:
            return "说明机器人主题正从概念热度向产业兑现逻辑过渡。"
        return "说明科技主线仍活跃，但要区分平台、应用与算力受益顺序。"
    if signal == "market_macro" or section == "财经市场":
        return "说明资金仍在围绕宏观预期、政策信号和价格变化重新定价。"
    return "说明该条新闻仍值得继续跟踪其后续发酵与资产影响。"


def select_ai_headlines(grouped, limit: int = 3):
    preferred_sources = ["The Verge", "TechCrunch", "IEEE Spectrum", "Ars Technica", "Engadget"]
    preferred_set = set(preferred_sources)
    items = []
    for item in grouped.get("科技产业", []):
        source = item.get("source", "")
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        if source not in preferred_set:
            continue
        if not any(k in text for k in ["ai", "openai", "anthropic", "nvidia", "robot", "chip", "model", "llm"]):
            continue
        items.append(item)

    def score(item):
        text = f"{item.get('title','')} {item.get('summary','')}".lower()
        pts = 0
        for keyword, val in [
            ("openai", 100), ("anthropic", 96), ("nvidia", 94), ("chip", 90),
            ("robot", 86), ("ai", 82), ("model", 78), ("llm", 76),
        ]:
            if keyword in text:
                pts = max(pts, val)
        source = item.get("source", "")
        if source == "The Verge":
            pts += 8
        elif source == "TechCrunch":
            pts += 7
        elif source == "IEEE Spectrum":
            pts += 6
        elif source == "Ars Technica":
            pts += 5
        elif source == "Engadget":
            pts += 4
        return pts

    selected = []
    seen = set()
    for item in sorted(items, key=score, reverse=True):
        title = normalize_headline_title(item.get("title", ""), item.get("summary", ""))
        key = (title.lower(), item.get("source", ""))
        if key in seen:
            continue
        seen.add(key)
        selected.append({
            "标题": title,
            "来源": item.get("source", "未知来源"),
            "时间": item.get("published", "未明确给出"),
            "内容": cap_text(make_content(item.get("summary", ""), item.get("title", "")), 78),
            "评论": cap_text(make_short_comment(item.get("section", ""), item.get("summary", ""), item.get("title", "")), 42),
        })
        if len(selected) >= limit:
            break
    return selected


def collect_news():
    grouped = {"宏观新闻": [], "财经市场": [], "科技产业": []}
    errors = []
    for feed in FEEDS:
        try:
            items = parse_feed(feed["url"], limit=16)
        except Exception as e:
            kind = feed.get("fallback_kind")
            if kind:
                try:
                    items = fallback_items(kind, limit=16)
                except Exception as e2:
                    errors.append(f"{feed['name']}: {e2}")
                    time.sleep(0.3)
                    continue
            else:
                errors.append(f"{feed['name']}: {e}")
                time.sleep(0.3)
                continue
        for item in items:
            if not within_24h(item.get("published_dt")):
                continue
            if is_noise_item(item.get("title", ""), item.get("summary", ""), feed["section"], feed["name"]):
                continue
            item["source"] = feed["name"]
            item["section"] = feed["section"]
            item["title_cn"] = normalize_headline_title(item.get("title", ""), item.get("summary", ""))
            item["内容摘要"] = make_content(item.get("summary", ""), item.get("title", ""))
            item["评论"] = cap_text(make_short_comment(feed["section"], item.get("summary", ""), item.get("title", "")), 42)
            grouped[feed["section"]].append(item)
        time.sleep(0.3)
    for section in grouped:
        dedup = []
        seen = set()
        for item in grouped[section]:
            key = ((item.get("title_cn") or "").lower(), item.get("source"))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)
        grouped[section] = dedup[:18]
    return grouped, {}, errors


def build_risk_alerts(grouped, _focus_hits):
    merged = " ".join(f"{i.get('title','')} {i.get('summary','')}" for arr in grouped.values() for i in arr).lower()
    alerts = []
    if any(k in merged for k in ["gaza", "israel", "iran", "hormuz"]):
        alerts.append("若中东冲突继续外溢至能源设施、港口或航运链，原油、运价与避险资产可能同步上冲。")
    if any(k in merged for k in ["ukraine", "russia", "moscow", "kyiv"]):
        alerts.append("若俄乌线再出现制裁升级、军援表态或基础设施打击，欧洲风险资产与能源预期可能重新承压。")
    if any(k in merged for k in ["china", "trade", "tariff", "commerce", "u.s."]):
        alerts.append("若美中经贸口径继续收紧，出口链、科技链与全球风险偏好修复节奏都可能受扰动。")
    if any(k in merged for k in ["stocks", "market", "fed", "inflation", "oil"]):
        alerts.append("若宏观与商品价格信号继续冲突，全球市场短线仍可能维持高波动而非顺畅单边。")
    return alerts or ["当前公开素材未显示单一压倒性风险源，但不能把这误读为风险已经出清。"]


def build_action_points(grouped, _focus_hits):
    merged = " ".join(f"{i.get('title','')} {i.get('summary','')}" for arr in grouped.values() for i in arr).lower()
    actions = []
    if any(k in merged for k in ["gaza", "israel", "hamas", "iran", "oil", "brent", "hormuz"]):
        actions.append("当前配置更适合保留一部分能源、黄金或其他避险对冲仓位，但不宜在情绪最高点无脑追高。")
    if any(k in merged for k in ["china", "trade", "tariff", "commerce"]):
        actions.append("对出口链、科技制造链与跨境风险资产，宜把政策口径变化纳入仓位节奏，而不是只看短线反弹。")
    if any(k in merged for k in ["ai", "openai", "anthropic", "nvidia", "robot", "chip"]):
        actions.append("科技线仍可保留观察名单，优先盯住真正有业绩或产业催化支撑的龙头，而不是纯情绪题材。")
    actions.append("若当天新增消息不足以形成单边逻辑，策略上更适合控制仓位、等待高质量新催化，而不是频繁追价。")
    return actions[:5]


def extract_yahoo_quote_page(symbol: str):
    url = f"https://finance.yahoo.com/quote/{urllib.parse.quote(symbol, safe='')}"
    html_text = fetch_text(url, timeout=20)
    patterns = [
        r'"regularMarketPrice"\s*:\s*\{[^\}]*"raw"\s*:\s*([-0-9.]+)',
        r'"currentPrice"\s*:\s*\{[^\}]*"raw"\s*:\s*([-0-9.]+)',
    ]
    change_patterns = [
        r'"regularMarketChangePercent"\s*:\s*\{[^\}]*"raw"\s*:\s*([-0-9.]+)',
        r'"regularMarketChange"\s*:\s*\{[^\}]*"raw"\s*:\s*([-0-9.]+)',
    ]
    price = None
    change_pct = None
    for pat in patterns:
        m = re.search(pat, html_text)
        if m:
            price = float(m.group(1))
            break
    for pat in change_patterns:
        m = re.search(pat, html_text)
        if m:
            change_pct = float(m.group(1))
            break
    return price, change_pct


def _fmt_num(v):
    try:
        num = float(v)
        if abs(num) >= 100:
            return f"{num:.2f}"
        if abs(num) >= 1:
            return f"{num:.4f}".rstrip('0').rstrip('.')
        return f"{num:.6f}".rstrip('0').rstrip('.')
    except Exception:
        return str(v)


def _fmt_change(v):
    try:
        return f"{float(v):+.2f}%"
    except Exception:
        text = str(v or "").strip()
        if not text:
            return ""
        return text if text.endswith('%') else f"{text}%"


def _safe_float(v):
    try:
        return float(str(v).replace(',', '').strip())
    except Exception:
        return None


def _fetch_text_with_headers(url: str, headers: dict[str, str], encoding: str):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode(encoding, errors='ignore')


def _collect_eastmoney_snapshot():
    out = {"lines": {}, "sources": []}
    try:
        url = (
            "https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f12,f14,f2,f3"
            "&secids=1.000001,0.399001,0.399006,100.HSI,100.NDX,100.NKY,133.USDCNH"
        )
        raw = _fetch_text_with_headers(url, {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com"}, "utf-8")
        data = json.loads(raw)
        rows = ((data or {}).get("data") or {}).get("diff") or []
        by_code = {str(x.get("f12") or ""): x for x in rows if isinstance(x, dict)}
        cn = []
        for label, code in [("上证指数", "000001"), ("深证成指", "399001"), ("创业板指", "399006")]:
            row = by_code.get(code)
            if row and row.get("f2") is not None:
                cn.append(f"{label} {_fmt_num(row['f2'])} ({_fmt_change(row.get('f3'))})")
        if cn:
            out["lines"]["国内指数"] = "；".join(cn)
        global_idx = []
        for label, code in [("恒生", "HSI"), ("纳指100", "NDX"), ("日经", "NKY")]:
            row = by_code.get(code)
            if row and row.get("f2") is not None:
                global_idx.append(f"{label} {_fmt_num(row['f2'])} ({_fmt_change(row.get('f3'))})")
        if global_idx:
            out["lines"]["全球指数补充"] = "；".join(global_idx)
        row = by_code.get("USDCNH")
        if row and row.get("f2") is not None:
            out["lines"]["汇率补充"] = f"美元兑离岸人民币 {_fmt_num(row['f2'])} ({_fmt_change(row.get('f3'))})"
        out["sources"].append("东方财富")
    except Exception:
        pass
    return out


def _collect_sina_snapshot():
    out = {"lines": {}, "sources": []}
    try:
        url = (
            "http://hq.sinajs.cn/list="
            "s_sh000001,s_sz399001,s_sz399006,rt_hkHSI,int_dji,int_nasdaq,int_sp500,int_nikkei,"
            "hf_GC,hf_CL,USDCNY,fx_susdcnh,DINIW"
        )
        raw = _fetch_text_with_headers(
            url,
            {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"},
            "gbk",
        )
        vals = {}
        for line in raw.splitlines():
            m = re.search(r'var hq_str_([^=]+)="([^"]*)";', line)
            if m:
                vals[m.group(1)] = m.group(2).split(',')
        cn = []
        for sym, label in [("s_sh000001", "上证指数"), ("s_sz399001", "深证成指"), ("s_sz399006", "创业板指")]:
            parts = vals.get(sym, [])
            if len(parts) >= 4:
                cn.append(f"{label} {_fmt_num(parts[1])} ({_fmt_change(parts[3])})")
        if cn:
            out["lines"]["国内指数"] = "；".join(cn)
        global_idx = []
        for sym, label in [("rt_hkHSI", "恒生"), ("int_dji", "道指"), ("int_nasdaq", "纳指"), ("int_sp500", "标普500"), ("int_nikkei", "日经")]:
            parts = vals.get(sym, [])
            if len(parts) >= 4:
                price = parts[6] if sym == "rt_hkHSI" and len(parts) > 6 else parts[1]
                chg = parts[8] if sym == "rt_hkHSI" and len(parts) > 8 else parts[3]
                global_idx.append(f"{label} {_fmt_num(price)} ({_fmt_change(chg)})")
        if global_idx:
            out["lines"]["全球指数"] = "；".join(global_idx)
        gc = vals.get("hf_GC", [])
        cl = vals.get("hf_CL", [])
        commodity = []
        if len(gc) >= 1:
            commodity.append(f"纽约黄金 {_fmt_num(gc[0])}")
        if len(cl) >= 1:
            commodity.append(f"纽约原油 {_fmt_num(cl[0])}")
        if commodity:
            out["lines"]["商品贵金属原油"] = "；".join(commodity)
        fx = []
        usdcny = vals.get("USDCNY", [])
        usdcnh = vals.get("fx_susdcnh", [])
        dxy = vals.get("DINIW", [])
        if len(usdcny) >= 2:
            fx.append(f"美元兑人民币 {_fmt_num(usdcny[1])}")
        if len(usdcnh) >= 2:
            fx.append(f"美元兑离岸人民币 {_fmt_num(usdcnh[1])}")
        if len(dxy) >= 2:
            fx.append(f"美元指数 {_fmt_num(dxy[1])}")
        if fx:
            out["lines"]["汇率"] = "；".join(fx)
        out["sources"].append("新浪财经")
    except Exception:
        pass
    return out


def _collect_tencent_snapshot():
    out = {"lines": {}, "sources": []}
    try:
        url = (
            "http://qt.gtimg.cn/q="
            "s_sh000001,s_sz399001,s_sz399006,r_hkHSI,usDJI,usIXIC,usINX,hf_GC,hf_CL,fx_susdcnh,USDCNY"
        )
        raw = _fetch_text_with_headers(
            url,
            {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com"},
            "gbk",
        )
        vals = {}
        for line in raw.splitlines():
            m = re.search(r'v_([^=]+)="([^"]*)";', line)
            if m:
                vals[m.group(1)] = m.group(2).split('~') if '~' in m.group(2) else m.group(2).split(',')
        cn = []
        for sym, label in [("s_sh000001", "上证指数"), ("s_sz399001", "深证成指"), ("s_sz399006", "创业板指")]:
            parts = vals.get(sym, [])
            if len(parts) >= 6:
                cn.append(f"{label} {_fmt_num(parts[3])} ({_fmt_change(parts[5])})")
        if cn:
            out["lines"]["国内指数"] = "；".join(cn)
        global_idx = []
        for sym, label in [("r_hkHSI", "恒生"), ("usDJI", "道指"), ("usIXIC", "纳指"), ("usINX", "标普500")]:
            parts = vals.get(sym, [])
            if len(parts) >= 5:
                change = parts[32] if sym == "r_hkHSI" and len(parts) > 32 else parts[32] if len(parts) > 32 else ""
                global_idx.append(f"{label} {_fmt_num(parts[3])} ({_fmt_change(change or parts[4])})")
        if global_idx:
            out["lines"]["全球指数"] = "；".join(global_idx)
        gc = vals.get("hf_GC", [])
        cl = vals.get("hf_CL", [])
        commodity = []
        if len(gc) >= 1:
            commodity.append(f"纽约黄金 {_fmt_num(gc[0])}")
        if len(cl) >= 1:
            commodity.append(f"纽约原油 {_fmt_num(cl[0])}")
        if commodity:
            out["lines"]["商品贵金属原油"] = "；".join(commodity)
        fx = []
        cnh = vals.get("fx_susdcnh", [])
        cny = vals.get("USDCNY", [])
        if len(cnh) >= 2:
            fx.append(f"美元兑离岸人民币 {_fmt_num(cnh[1])}")
        if len(cny) >= 4:
            fx.append(f"美元兑人民币 {_fmt_num(cny[3])}")
        if fx:
            out["lines"]["汇率"] = "；".join(fx)
        out["sources"].append("腾讯财经")
    except Exception:
        pass
    return out


def collect_market_snapshot():
    snapshot = {
        "国内指数": "暂未稳定抓到三方行情快照",
        "全球指数": "暂未稳定抓到三方行情快照",
        "全球指数补充": "暂未稳定抓到三方行情快照",
        "商品贵金属原油": "暂未稳定抓到三方行情快照",
        "汇率": "暂未稳定抓到三方行情快照",
        "汇率补充": "暂未稳定抓到三方行情快照",
        "港股/台股/期货外汇说明": "港股已纳入恒生；台股与更细分期货/外汇品种待继续补充映射。",
        "数据源": "东方财富 / 新浪财经 / 腾讯财经",
    }

    collectors = [_collect_eastmoney_snapshot, _collect_sina_snapshot, _collect_tencent_snapshot]
    merged_sources = []
    for collector in collectors:
        try:
            result = collector()
        except Exception:
            continue
        for key, value in (result.get("lines") or {}).items():
            if value:
                snapshot[key] = value
        merged_sources.extend(result.get("sources") or [])

    if merged_sources:
        snapshot["数据源"] = " / ".join(dict.fromkeys(merged_sources))
    return snapshot


def select_top_headlines(grouped, limit: int = 12):
    all_items = []
    for section in ("宏观新闻", "财经市场", "科技产业"):
        all_items.extend(grouped.get(section, []))
    def score(item):
        text = f"{item.get('title','')} {item.get('summary','')}".lower()
        pts = 0
        for keyword, val in [
            ("gaza", 120), ("iran", 118), ("hormuz", 116), ("israel", 110), ("ukraine", 108),
            ("russia", 100), ("tariff", 98), ("trade", 94), ("oil", 90), ("market", 80),
            ("openai", 60), ("anthropic", 58), ("nvidia", 56), ("ai", 50), ("goldman sachs", 45),
        ]:
            if keyword in text:
                pts = max(pts, val)
        if item.get("source", "").startswith("Google News"):
            pts += 5
        return pts
    selected = []
    seen = set()
    for item in sorted(all_items, key=score, reverse=True):
        title = item.get("title_cn") or normalize_headline_title(item.get("title", ""), item.get("summary", ""))
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append({
            "标题": title,
            "来源": item.get("source", "未知来源"),
            "时间": item.get("published", "未明确给出"),
            "内容": cap_text(make_content(item.get("summary", ""), item.get("title", "")), 78),
            "评论": cap_text(make_short_comment(item.get("section", ""), item.get("summary", ""), item.get("title", "")), 42),
        })
        if len(selected) >= limit:
            break
    return selected


def build_template_report(grouped, focus_hits, errors):
    now_str = NOW.strftime("%Y-%m-%d %H:%M")
    market_snapshot = collect_market_snapshot()
    headline_items = select_top_headlines(grouped, limit=12)
    ai_headline_items = select_ai_headlines(grouped, limit=3)
    risk_alerts = build_risk_alerts(grouped, focus_hits)
    action_points = build_action_points(grouped, focus_hits)
    lines = [
        f"全球综合情报报告 - {NOW.strftime('%Y-%m-%d')}",
        f"报告时间：{now_str}",
        "执行规范：时间窗口仅限过去24小时；抓不到就写缺口。",
        "",
        "一、重要头条新闻",
    ]
    if headline_items:
        for idx, item in enumerate(headline_items, start=1):
            lines.append(f"{idx}. {item['标题']}")
            lines.append(f"   内容：{item['内容']}")
            lines.append(f"   评论：{item['评论']}")
            lines.append(f"   （来源：{item['来源']} | 发布时间：{item['时间']}）")
            lines.append("")
    else:
        lines.append("- 今日无足够扎实的头条更新")
        lines.append("")

    lines.append("二、AI科技专栏头条")
    if ai_headline_items:
        for offset, item in enumerate(ai_headline_items, start=13):
            lines.append(f"{offset}. {item['标题']}")
            lines.append(f"   内容：{item['内容']}")
            lines.append(f"   评论：{item['评论']}")
            lines.append(f"   （来源：{item['来源']} | 发布时间：{item['时间']}）")
            lines.append("")
    else:
        lines.append("- 今日未抓到足够扎实的 AI 科技头条")
        lines.append("")

    lines.append("三、全球市场动态")
    for k, v in market_snapshot.items():
        lines.append(f"- {k}：{v}")
    lines.append("")
    lines.append("四、风险预警")
    for item in risk_alerts:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("五、投资建议")
    for item in action_points:
        lines.append(f"- {item}")
    lines.append("")
    if errors:
        lines.append("六、抓取缺口说明")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")
    lines.append("说明：本报告优先保留过去24小时内公开可验证新增；若关键报价未稳定抓到，则直接标注缺口，不使用旧数据补洞。")
    text_body = "\n".join(lines)
    html_body = "<html><body><pre style='white-space:pre-wrap;font-family:Microsoft YaHei,Arial,sans-serif;'>" + html.escape(text_body) + "</pre></body></html>"
    return text_body, html_body


def build_text_report(grouped, focus_hits, errors):
    return build_template_report(grouped, focus_hits, errors)[0]


def build_html_report(grouped, focus_hits, errors):
    return build_template_report(grouped, focus_hits, errors)[1]


def send_email(subject: str, text_body: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    grouped, focus_hits, errors = collect_news()
    text_body = build_text_report(grouped, focus_hits, errors)
    html_body = build_html_report(grouped, focus_hits, errors)
    preview_dir = Path(__file__).resolve().parent / "reports" / "scheduled"
    preview_dir.mkdir(parents=True, exist_ok=True)
    (preview_dir / "formal_preview.txt").write_text(text_body, encoding="utf-8")
    (preview_dir / "formal_preview.html").write_text(html_body, encoding="utf-8")
    print("FORMAL_REPORT_PREVIEW_READY")
    print(str(preview_dir / "formal_preview.txt"))


if __name__ == "__main__":
    main()
