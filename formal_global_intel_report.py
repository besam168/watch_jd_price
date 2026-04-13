import smtplib
import ssl
import json
import sys
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate
from datetime import datetime, timezone, timedelta
import urllib.request
import xml.etree.ElementTree as ET
import html
import re
import time
from email.utils import parsedate_to_datetime

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "910633260@qq.com"
SMTP_PASSWORD = "sghqeeeeyuzjbcbb"
RECIPIENTS = ["besam168168@gmail.com", "758622673@qq.com"]

TZ_CN = timezone(timedelta(hours=8))
NOW = datetime.now(TZ_CN)
WINDOW_START = NOW - timedelta(hours=24)

FEEDS = [
    {"name": "路透世界", "url": "https://feeds.reuters.com/Reuters/worldNews", "section": "宏观新闻"},
    {"name": "美联社头条", "url": "https://feeds.ap.org/apf-topnews", "section": "宏观新闻"},
    {"name": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "section": "宏观新闻"},
    {"name": "半岛电视台", "url": "https://www.aljazeera.com/xml/rss/all.xml", "section": "宏观新闻"},
    {"name": "CNBC国际", "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "section": "财经市场"},
    {"name": "雅虎财经", "url": "https://finance.yahoo.com/news/rssindex", "section": "财经市场"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "section": "科技产业"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "section": "科技产业"},
]

KEYWORDS = {
    "加沙/以色列/哈马斯": ["gaza", "israel", "hamas", "rafah"],
    "乌克兰/俄罗斯": ["ukraine", "russia", "kyiv", "moscow"],
    "美中贸易/关税/商业": ["china", "u.s.", "us-china", "tariff", "trade", "commerce"],
}


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClawFormalIntelV3/1.0"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


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
    if not dt:
        return False
    return WINDOW_START <= dt <= NOW


def parse_feed(url: str, limit: int = 10):
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
            pub_dt = parse_time(pub)
            items.append({"title": title, "link": link, "summary": desc, "published": pub, "published_dt": pub_dt})
        return items
    ns_atom = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{ns_atom}entry")[:limit]:
        title = strip_html(entry.findtext(f"{ns_atom}title", default=""))
        summary = strip_html(entry.findtext(f"{ns_atom}summary", default="") or entry.findtext(f"{ns_atom}content", default=""))
        published = strip_html(entry.findtext(f"{ns_atom}updated", default="") or entry.findtext(f"{ns_atom}published", default=""))
        pub_dt = parse_time(published)
        link = ""
        for link_node in entry.findall(f"{ns_atom}link"):
            href = link_node.attrib.get("href", "").strip()
            rel = link_node.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                link = href
                break
        items.append({"title": title, "link": link, "summary": summary, "published": published, "published_dt": pub_dt})
    return items


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
        (("hormuz",), "霍尔木兹海峡风险再度牵动全球能源预期"),
        (("iran", "blockade"), "伊朗相关封锁风险推升能源与地缘担忧"),
        (("oil",), "国际油价与能源风险溢价继续升温"),
        (("gaza",), "加沙局势仍牵动中东风险定价"),
        (("israel",), "以色列相关动态继续牵动中东局势"),
        (("ukraine",), "俄乌局势仍在持续发酵"),
        (("russia",), "俄罗斯相关动态继续牵动欧洲安全预期"),
        (("openai",), "OpenAI 新动向继续牵动科技板块预期"),
        (("anthropic",), "Anthropic 动向继续反映企业级 AI 竞争"),
        (("nvidia",), "NVIDIA 相关动态继续影响算力板块"),
        (("robot",), "机器人主题继续升温"),
        (("ai",), "AI 产业动态继续升温"),
        (("goldman sachs",), "高盛业绩与投行业务恢复情况受市场关注"),
        (("budapest", "moscow"), "欧洲政治动向与莫斯科反应形成落差"),
    ]
    for keywords, zh in rules:
        if all(k in lower for k in keywords):
            return zh
    cleaned = re.sub(r"\s+", " ", raw).strip(" -|:;,.，。；：")
    if re.search(r"[\u4e00-\u9fff]", cleaned):
        return cleaned
    return "国际要闻更新"


def chineseize_summary(text: str) -> str:
    text = strip_html(text)
    if not text:
        return "今日仅抓到标题级线索，建议继续复核正文。"
    lower = text.lower()
    rules = [
        (("tariff", "china"), "美国对华关税口径继续收紧，说明经贸摩擦仍可能扰动出口链、科技链与全球风险偏好。"),
        (("hormuz", "blockade"), "霍尔木兹相关封锁风险若继续升温，最直接的冲击会落在原油、航运和避险资产上。"),
        (("oil", "price"), "油价上行反映市场仍在计入地缘冲突外溢与供应扰动的风险溢价。"),
        (("gaza",), "加沙局势若继续升级，市场会重新评估中东风险外溢与避险需求。"),
        (("ukraine",), "俄乌相关动态说明欧洲安全风险仍未退出主要视野。"),
        (("openai",), "OpenAI 的动作显示大模型竞争仍在加速，市场继续关注商业化和落地节奏。"),
        (("anthropic",), "Anthropic 相关动态反映企业级 AI 竞争仍在深化。"),
        (("nvidia",), "NVIDIA 动向继续影响算力资本开支与科技股风险偏好。"),
        (("robot",), "机器人主题热度延续，市场继续关注真实商用落地。"),
        (("ai",), "AI 仍是科技板块主线之一，重点在采用速度、产品化与真实付费场景。"),
        (("goldman sachs",), "高盛最新业绩与业务恢复情况被市场重点关注，金融权重股表现仍会影响风险偏好。"),
        (("president donald trump",), "特朗普相关表态继续扰动市场对关税、能源与外交政策的预期。"),
        (("automaker",), "汽车产业相关动态反映企业仍在争夺销量、成本与技术路线优势。"),
    ]
    for keywords, zh in rules:
        if all(k in lower for k in keywords):
            return zh
    if re.search(r"[\u4e00-\u9fff]", text):
        return cap_text(text, 60)
    return "该条目有新增，但当前仅抓到英文摘要线索，需结合正文进一步复核其市场含义。"


def make_content(summary: str, title: str) -> str:
    return cap_text(chineseize_summary(summary or title or ""), 70)


def make_conclusion(section: str, summary: str, title: str) -> str:
    base = f"{title} {summary}".lower()
    if section == "宏观新闻":
        if any(k in base for k in ["gaza", "israel", "iran", "ukraine", "russia"]):
            return "地缘政治仍是当前最容易触发全球风险偏好再定价的变量，需继续盯住官方表态与冲突外溢。"
        if any(k in base for k in ["tariff", "trade", "china"]):
            return "经贸与政策口径仍可能扰动全球供应链预期，市场对风险资产的容忍度不会太高。"
        return "该宏观条目有跟踪价值，但暂未显示足以单独扭转全球资产定价的决定性新变量。"
    if section == "财经市场":
        if any(k in base for k in ["oil", "hormuz", "blockade", "market", "stocks", "bond"]):
            return "市场仍在围绕能源、风险偏好与宏观预期重新定价，短线高波动特征尚未解除。"
        return "该财经动态更多体现边际变化，需结合后续价格与成交反馈再判断持续性。"
    if any(k in base for k in ["openai", "anthropic", "nvidia", "ai", "robot", "chip"]):
        return "科技主线仍有效，但更应区分真正有产业兑现能力的方向与纯情绪炒作。"
    return "该科技条目反映行业仍在演进，但是否形成更强行情，还要看后续产品化与业绩验证。"


def classify_topic(item) -> str | None:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    if any(k in text for k in ["gaza", "israel", "hamas", "rafah", "iran", "hormuz", "houthi"]):
        return "中东"
    if any(k in text for k in ["ukraine", "russia", "kyiv", "moscow"]):
        return "俄乌"
    if any(k in text for k in ["china", "tariff", "trade", "commerce", "u.s."]):
        return "中美关系"
    return None


def collect_news():
    grouped = {"宏观新闻": [], "财经市场": [], "科技产业": []}
    focus_hits = {k: [] for k in KEYWORDS}
    errors = []
    for feed in FEEDS:
        try:
            items = parse_feed(feed["url"], limit=10)
            for item in items:
                if not within_24h(item.get("published_dt")):
                    continue
                item["source"] = feed["name"]
                item["section"] = feed["section"]
                item["title_cn"] = title_to_cn(item.get("title", ""))
                item["内容摘要"] = make_content(item.get("summary", ""), item.get("title", ""))
                item["结论"] = make_conclusion(feed["section"], item.get("summary", ""), item.get("title", ""))
                grouped[feed["section"]].append(item)
                merged = f"{item.get('title', '')} {item.get('summary', '')}".lower()
                for topic, words in KEYWORDS.items():
                    if any(w in merged for w in words):
                        focus_hits[topic].append(item)
        except Exception as e:
            errors.append(f"{feed['name']}: {e}")
        time.sleep(0.5)
    for section in grouped:
        grouped[section] = grouped[section][:6]
    for topic in focus_hits:
        dedup = []
        seen = set()
        for item in focus_hits[topic]:
            key = (item.get("title_cn") or item.get("title"), item.get("source"))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)
        focus_hits[topic] = dedup[:4]
    return grouped, focus_hits, errors


def summarize_signals(grouped, focus_hits):
    total = sum(len(v) for v in grouped.values())
    macro_count = len(grouped.get("宏观新闻", []))
    market_count = len(grouped.get("财经市场", []))
    tech_count = len(grouped.get("科技产业", []))
    middle_east_count = len(focus_hits.get("加沙/以色列/哈马斯", []))
    russia_count = len(focus_hits.get("乌克兰/俄罗斯", []))
    us_china_count = len(focus_hits.get("美中贸易/关税/商业", []))
    summary_points = []
    if middle_east_count:
        summary_points.append("中东相关条目仍有新增，地缘风险溢价尚未完全退潮。")
    elif russia_count:
        summary_points.append("俄乌线仍有更新，欧洲安全与能源预期仍需跟踪。")
    else:
        summary_points.append("地缘主线暂无密集新增，但这更像信息空窗，不代表风险消失。")
    if us_china_count:
        summary_points.append("美中贸易/关税线有新增，供应链与风险偏好仍可能受政策口径扰动。")
    elif market_count >= 3:
        summary_points.append("财经市场条目相对更活跃，说明资金更关注宏观与资产价格方向。")
    else:
        summary_points.append("财经市场新增不算密集，当前更适合把行情理解为等待新催化。")
    if tech_count >= 3:
        summary_points.append("科技板块素材较充分，说明 AI 与平台/硬件仍是重要关注方向。")
    else:
        summary_points.append("科技板块新增有限，短线仍更容易被宏观与地缘主线压制。")
    summary_points.append(f"本轮共纳入 {total} 条公开资讯，其中宏观 {macro_count} 条、市场 {market_count} 条、科技 {tech_count} 条。")
    return summary_points


def build_focus_assessment(title: str, items):
    if not items:
        return "过去24小时未抓到足够扎实的新条目，当前更适合维持跟踪而不是做过度推断。"
    titles = " ".join((item.get("title") or "") for item in items).lower()
    if title == "中东":
        return "中东线仍具扰动性，若后续再出现军事升级、能源设施受威胁或人道冲突加剧，油价与避险情绪都可能迅速放大。"
    if title == "俄乌":
        return "俄乌线说明欧洲安全议题没有降温，后续若伴随制裁、军援或能源表态，市场仍会重新计价。"
    if title == "中美关系":
        return "美中经贸线若继续升温，最直接的冲击通常落在出口链、科技链和风险偏好修复节奏上。"
    return "该专题已有新增，但还需继续跟踪后续官方表态与市场反馈。"


def build_section_assessment(section: str, items):
    if not items:
        if section == "宏观新闻":
            return "本节今日素材不足，说明当前公开信息里暂未形成足够强的新宏观主线。"
        if section == "财经市场":
            return "本节今日素材不足，市场暂时更像在等待更明确的政策或风险事件催化。"
        return "本节今日素材不足，科技方向仍可跟踪，但短线未见特别强的新催化。"
    merged = " ".join(f"{item.get('title', '')} {item.get('summary', '')}" for item in items).lower()
    if section == "宏观新闻":
        if any(k in merged for k in ["gaza", "israel", "hamas", "ukraine", "russia", "tariff", "trade"]):
            return "宏观主线仍由地缘政治与经贸口径驱动，风险偏好容易被突发事件反复拉扯。"
        return "宏观条目有更新，但暂未看到足以单独重定价全球资产的大级别新增变量。"
    if section == "财经市场":
        if any(k in merged for k in ["stocks", "market", "fed", "oil", "bond", "tariff", "trade", "hormuz"]):
            return "财经市场板块说明资金仍在围绕宏观预期、风险偏好与商品价格重新定价。"
        return "财经条目存在，但更多是边际变化，尚不足以形成单边市场共识。"
    return "科技板块仍围绕 AI、芯片和平台竞争展开，说明成长线尚未退出核心关注。"


def build_risk_alerts(grouped, focus_hits):
    merged = " ".join(
        f"{item.get('title', '')} {item.get('summary', '')}" 
        for section_items in list(grouped.values()) + list(focus_hits.values())
        for item in section_items
    ).lower()
    alerts = []
    if any(k in merged for k in ["gaza", "israel", "hamas", "rafah", "iran", "houthi", "hormuz"]):
        alerts.append("若中东冲突继续外溢至能源设施、港口或航运链，原油、运价与避险资产可能同步上冲。")
    if any(k in merged for k in ["ukraine", "russia", "moscow", "kyiv"]):
        alerts.append("若俄乌线再出现制裁升级、军援表态或基础设施打击，欧洲风险资产与能源预期可能重新承压。")
    if any(k in merged for k in ["china", "trade", "tariff", "commerce", "u.s."]):
        alerts.append("若美中经贸口径继续收紧，出口链、科技链与全球风险偏好修复节奏都可能受扰动。")
    if any(k in merged for k in ["stocks", "market", "fed", "inflation", "oil"]):
        alerts.append("若宏观与商品价格信号继续冲突，全球市场短线仍可能维持高波动而非顺畅单边。")
    return alerts or ["当前公开素材未显示单一压倒性风险源，但这更像信息空窗，不能把它误读为风险出清。"]


def build_action_points(grouped, focus_hits):
    merged = " ".join(
        f"{item.get('title', '')} {item.get('summary', '')}" 
        for section_items in list(grouped.values()) + list(focus_hits.values())
        for item in section_items
    ).lower()
    actions = []
    if any(k in merged for k in ["gaza", "israel", "hamas", "iran", "oil", "brent", "hormuz"]):
        actions.append("当前配置更适合保留一部分能源、黄金或其他避险对冲仓位，但不宜在情绪最高点无脑追高。")
    if any(k in merged for k in ["china", "trade", "tariff", "commerce"]):
        actions.append("对出口链、科技制造链与跨境风险资产，宜把政策口径变化纳入仓位节奏，而不是只看短线反弹。")
    if any(k in merged for k in ["ai", "openai", "anthropic", "nvidia", "robot", "chip"]):
        actions.append("科技线仍可保留观察名单，优先盯住真正有业绩或产业催化支撑的龙头，而不是纯情绪题材。")
    actions.append("若当天新增消息不足以形成单边逻辑，策略上更适合控制仓位、等待高质量新催化，而不是频繁追价。")
    return actions[:5]


def collect_market_snapshot():
    snapshot = {
        "美股指数": "暂未稳定抓到权威快照",
        "黄金": "暂未稳定抓到权威快照",
        "布伦特原油": "暂未稳定抓到权威快照",
        "汇率": "暂未稳定抓到权威快照",
    }
    try:
        raw = fetch_url("https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EGSPC,%5EDJI,%5EIXIC,GC%3DF,BZ%3DF,CNY%3DX,DX-Y.NYB", timeout=20).decode("utf-8", errors="ignore")
        data = json.loads(raw)
        results = (((data or {}).get("quoteResponse") or {}).get("result") or [])
        by_symbol = {str(item.get("symbol") or ""): item for item in results if isinstance(item, dict)}
        if by_symbol:
            parts = []
            for label, key in [("标普500", "^GSPC"), ("道指", "^DJI"), ("纳指", "^IXIC")]:
                obj = by_symbol.get(key)
                if obj and obj.get("regularMarketPrice") is not None:
                    parts.append(f"{label} {obj['regularMarketPrice']}")
            if parts:
                snapshot["美股指数"] = "；".join(parts)
            gold = by_symbol.get("GC=F")
            if gold and gold.get("regularMarketPrice") is not None:
                snapshot["黄金"] = f"近似 {gold['regularMarketPrice']}"
            brent = by_symbol.get("BZ=F")
            if brent and brent.get("regularMarketPrice") is not None:
                snapshot["布伦特原油"] = f"近似 {brent['regularMarketPrice']}"
            fx_parts = []
            cny = by_symbol.get("CNY=X")
            dxy = by_symbol.get("DX-Y.NYB")
            if cny and cny.get("regularMarketPrice") is not None:
                fx_parts.append(f"美元兑离岸人民币近似 {cny['regularMarketPrice']}")
            if dxy and dxy.get("regularMarketPrice") is not None:
                fx_parts.append(f"美元指数近似 {dxy['regularMarketPrice']}")
            if fx_parts:
                snapshot["汇率"] = "；".join(fx_parts)
    except Exception:
        pass
    return snapshot


def select_top_headlines(grouped, limit: int = 5):
    all_items = []
    for section in ("宏观新闻", "财经市场", "科技产业"):
        all_items.extend(grouped.get(section, []))
    def score(item):
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        pts = 0
        for keyword, val in [
            ("gaza", 120), ("iran", 118), ("hormuz", 116), ("israel", 110), ("ukraine", 108),
            ("russia", 100), ("tariff", 98), ("trade", 94), ("oil", 90), ("market", 80),
            ("openai", 60), ("anthropic", 58), ("nvidia", 56), ("ai", 50), ("goldman sachs", 45),
        ]:
            if keyword in text:
                pts = max(pts, val)
        return pts
    selected = []
    seen = set()
    for item in sorted(all_items, key=score, reverse=True):
        zh_title = item.get("title_cn") or title_to_cn(item.get("title", ""))
        if zh_title in seen:
            continue
        seen.add(zh_title)
        selected.append({
            "标题": zh_title,
            "来源": item.get("source", "未知来源"),
            "时间": item.get("published", "未明确给出"),
            "结论": cap_text(chineseize_summary(item.get("summary") or item.get("title") or ""), 52),
        })
        if len(selected) >= limit:
            break
    return selected


def build_template_a_report(grouped, focus_hits, errors):
    now_str = NOW.strftime("%Y-%m-%d %H:%M")
    market_snapshot = collect_market_snapshot()
    headline_items = select_top_headlines(grouped, limit=5)
    summary_points = summarize_signals(grouped, focus_hits)
    risk_alerts = build_risk_alerts(grouped, focus_hits)
    action_points = build_action_points(grouped, focus_hits)
    geo_buckets = {"中东": [], "俄乌": [], "中美关系": []}
    for section_items in grouped.values():
        for item in section_items:
            bucket = classify_topic(item)
            if bucket and len(geo_buckets[bucket]) < 2:
                if all((item.get("title_cn") or item.get("title")) != (x.get("title_cn") or x.get("title")) for x in geo_buckets[bucket]):
                    geo_buckets[bucket].append(item)
    geo_lines = []
    for title in ["中东", "俄乌", "中美关系"]:
        geo_lines.append((title, build_focus_assessment(title, geo_buckets[title]), geo_buckets[title]))
    industry_points = [
        ("全球宏观", build_section_assessment("宏观新闻", grouped["宏观新闻"])),
        ("财经市场", build_section_assessment("财经市场", grouped["财经市场"])),
        ("科技产业", build_section_assessment("科技产业", grouped["科技产业"])),
    ]
    text_lines = [
        f"全球综合情报报告 - {NOW.strftime('%Y-%m-%d')}",
        f"报告时间：{now_str}",
        "",
        "一、重要头条新闻",
    ]
    for idx, item in enumerate(headline_items, start=1):
        text_lines.append(f"{idx}. {item['标题']}（来源：{item['来源']} | 发布时间：{item['时间']}）")
        text_lines.append(f"   结论：{item['结论']}")
        text_lines.append("")
    text_lines.append("二、50字左右总判断")
    for point in summary_points:
        text_lines.append(f"- {point}")
    text_lines.append("")
    text_lines.append("三、全球市场动态")
    for k, v in market_snapshot.items():
        text_lines.append(f"- {k}：{v}")
    text_lines.append(f"- 市场判断：{build_section_assessment('财经市场', grouped['财经市场'])}")
    text_lines.append("")
    text_lines.append("四、地缘政治热点")
    for title, assessment, items in geo_lines:
        text_lines.append(f"【{title}】")
        text_lines.append(f"- 判断：{assessment}")
        if items:
            for item in items:
                text_lines.append(f"- 线索：{item.get('title_cn') or title_to_cn(item.get('title', ''))}（来源：{item.get('source', '未知来源')}）")
        else:
            text_lines.append("- 今日无重大更新")
        text_lines.append("")
    text_lines.append("五、全球经济与产业动态")
    for title, assessment in industry_points:
        text_lines.append(f"- {title}：{assessment}")
    text_lines.append("")
    text_lines.append("六、风险预警（24-48小时短期 / 中期 / 长期）")
    for item in risk_alerts:
        text_lines.append(f"- {item}")
    text_lines.append("")
    text_lines.append("七、投资建议")
    for item in action_points:
        text_lines.append(f"- {item}")
    text_lines.append("")
    text_lines.append("说明：本报告优先保留过去24小时内公开可验证新增；若关键报价未稳定抓到，则直接标注缺口，不使用旧数据补洞。")
    html_body = "<html><body><pre style='white-space:pre-wrap;font-family:Microsoft YaHei,Arial,sans-serif;'>" + html.escape("\n".join(text_lines)) + "</pre></body></html>"
    return "\n".join(text_lines), html_body


def build_text_report(grouped, focus_hits, errors):
    text_body, _ = build_template_a_report(grouped, focus_hits, errors)
    return text_body


def build_html_report(grouped, focus_hits, errors):
    _, html_body = build_template_a_report(grouped, focus_hits, errors)
    return html_body


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
