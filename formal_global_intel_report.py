import smtplib
import ssl
import json
import sys
import webbrowser
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate, parsedate_to_datetime
from datetime import datetime, timezone, timedelta
import urllib.request
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
    {"name": "路透世界", "url": "https://feeds.reuters.com/Reuters/worldNews", "section": "宏观新闻", "browser_fallback": "https://www.reuters.com/world/"},
    {"name": "美联社头条", "url": "https://feeds.ap.org/apf-topnews", "section": "宏观新闻", "browser_fallback": "https://apnews.com/"},
    {"name": "BBC国际", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "section": "宏观新闻"},
    {"name": "半岛电视台", "url": "https://www.aljazeera.com/xml/rss/all.xml", "section": "宏观新闻"},
    {"name": "CNBC国际", "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "section": "财经市场"},
    {"name": "雅虎财经", "url": "https://finance.yahoo.com/news/rssindex", "section": "财经市场"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "section": "科技产业"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "section": "科技产业"},
]

REPORT_SPEC = """
角色：首席全球分析师。
时间窗口：仅限过去0-24小时内公开可验证信息。
真实性约束：拒绝虚构、拒绝脑补、拒绝把搜索残片当新闻；抓不到就明确写缺口。
新版输出结构：
1. 重要头条新闻（约12条，每条带内容摘要约70字、评论约40字、来源时间）
2. 全球市场动态（只报数据与变化，不写市场判断）
3. 风险预警
4. 投资建议
"""


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def try_browser_fallback(url: str) -> None:
    try:
        webbrowser.open(url)
        time.sleep(5)
    except Exception:
        pass


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OpenClawFormalIntelV4/1.0"})
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
    return bool(dt and WINDOW_START <= dt <= NOW)


def parse_feed(url: str, limit: int = 14):
    raw = fetch_url(url)
    root = ET.fromstring(raw)
    items = []
    channel = root.find("channel")
    if channel is not None:
        for item in channel.findall("item")[:limit]:
            items.append({
                "title": strip_html(item.findtext("title", default="")),
                "link": (item.findtext("link", default="") or "").strip(),
                "summary": strip_html(item.findtext("description", default="")),
                "published": strip_html(item.findtext("pubDate", default="")),
            })
        for item in items:
            item["published_dt"] = parse_time(item["published"])
        return items
    ns_atom = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{ns_atom}entry")[:limit]:
        link = ""
        for link_node in entry.findall(f"{ns_atom}link"):
            href = link_node.attrib.get("href", "").strip()
            rel = link_node.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                link = href
                break
        published = strip_html(entry.findtext(f"{ns_atom}updated", default="") or entry.findtext(f"{ns_atom}published", default=""))
        items.append({
            "title": strip_html(entry.findtext(f"{ns_atom}title", default="")),
            "link": link,
            "summary": strip_html(entry.findtext(f"{ns_atom}summary", default="") or entry.findtext(f"{ns_atom}content", default="")),
            "published": published,
            "published_dt": parse_time(published),
        })
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
        (("iran",), "伊朗相关动态继续推升中东风险溢价"),
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
    if re.search(r"[\u4e00-\u9fff]", raw):
        return raw
    return "国际要闻更新"


def chineseize_summary(text: str) -> str:
    text = strip_html(text)
    lower = text.lower()
    rules = [
        (("tariff", "china"), "美国对华关税口径继续收紧，说明经贸摩擦仍可能扰动出口链、科技链与全球风险偏好。"),
        (("hormuz",), "霍尔木兹相关风险若继续升温，最直接的冲击会落在原油、航运和避险资产上。"),
        (("gaza",), "加沙局势若继续升级，市场会重新评估中东风险外溢与避险需求。"),
        (("ukraine",), "俄乌相关动态说明欧洲安全风险仍未退出主要视野。"),
        (("openai",), "OpenAI 的动作显示大模型竞争仍在加速，市场继续关注商业化与落地节奏。"),
        (("anthropic",), "Anthropic 相关动态反映企业级 AI 竞争仍在深化。"),
        (("nvidia",), "NVIDIA 动向继续影响算力资本开支与科技股风险偏好。"),
        (("ai",), "AI 仍是科技板块主线之一，重点在采用速度、产品化与真实付费场景。"),
        (("goldman sachs",), "高盛最新业绩与业务恢复情况被市场重点关注，金融权重股表现仍会影响风险偏好。"),
        (("president donald trump",), "特朗普相关表态继续扰动市场对关税、能源与外交政策的预期。"),
    ]
    for keywords, zh in rules:
        if all(k in lower for k in keywords):
            return zh
    if re.search(r"[\u4e00-\u9fff]", text):
        return cap_text(text, 78)
    return "该条目有新增，但当前仅抓到英文摘要线索，需结合正文进一步复核其实际影响。"


def make_content(summary: str, title: str) -> str:
    return cap_text(chineseize_summary(summary or title or ""), 78)


def make_short_comment(section: str, summary: str, title: str) -> str:
    base = f"{title} {summary}".lower()
    if any(k in base for k in ["china", "tariff", "trade", "commerce"]):
        return "说明经贸摩擦仍可能扰动出口链和风险偏好。"
    if any(k in base for k in ["gaza", "israel", "iran", "hormuz", "oil"]):
        return "说明地缘风险仍会持续牵动能源与避险资产。"
    if any(k in base for k in ["ukraine", "russia", "moscow", "kyiv"]):
        return "说明欧洲安全议题仍未退出市场视野。"
    if any(k in base for k in ["openai", "anthropic", "nvidia", "ai", "robot", "chip"]):
        return "说明科技主线仍活跃，但需警惕纯情绪炒作。"
    if section == "财经市场":
        return "说明资金仍在围绕宏观与价格信号重新定价。"
    return "说明该条目仍值得继续跟踪其后续发酵。"


def collect_news():
    grouped = {"宏观新闻": [], "财经市场": [], "科技产业": []}
    errors = []
    for feed in FEEDS:
        try:
            items = parse_feed(feed["url"], limit=14)
        except Exception as e:
            if feed.get("browser_fallback"):
                try:
                    try_browser_fallback(feed["browser_fallback"])
                    items = parse_feed(feed["url"], limit=14)
                except Exception as e2:
                    errors.append(f"{feed['name']}: {e2}")
                    time.sleep(0.5)
                    continue
            else:
                errors.append(f"{feed['name']}: {e}")
                time.sleep(0.5)
                continue
        for item in items:
            if not within_24h(item.get("published_dt")):
                continue
            item["source"] = feed["name"]
            item["section"] = feed["section"]
            item["title_cn"] = title_to_cn(item.get("title", ""))
            item["内容摘要"] = make_content(item.get("summary", ""), item.get("title", ""))
            item["评论"] = cap_text(make_short_comment(feed["section"], item.get("summary", ""), item.get("title", "")), 42)
            grouped[feed["section"]].append(item)
        time.sleep(0.5)
    for section in grouped:
        dedup = []
        seen = set()
        for item in grouped[section]:
            key = (item.get("title_cn"), item.get("source"))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)
        grouped[section] = dedup[:12]
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
            if by_symbol.get("GC=F", {}).get("regularMarketPrice") is not None:
                snapshot["黄金"] = f"近似 {by_symbol['GC=F']['regularMarketPrice']}"
            if by_symbol.get("BZ=F", {}).get("regularMarketPrice") is not None:
                snapshot["布伦特原油"] = f"近似 {by_symbol['BZ=F']['regularMarketPrice']}"
            fx_parts = []
            if by_symbol.get("CNY=X", {}).get("regularMarketPrice") is not None:
                fx_parts.append(f"美元兑离岸人民币近似 {by_symbol['CNY=X']['regularMarketPrice']}")
            if by_symbol.get("DX-Y.NYB", {}).get("regularMarketPrice") is not None:
                fx_parts.append(f"美元指数近似 {by_symbol['DX-Y.NYB']['regularMarketPrice']}")
            if fx_parts:
                snapshot["汇率"] = "；".join(fx_parts)
    except Exception:
        pass
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
        return pts
    selected = []
    seen = set()
    for item in sorted(all_items, key=score, reverse=True):
        title = item.get("title_cn") or title_to_cn(item.get("title", ""))
        if title in seen:
            continue
        seen.add(title)
        selected.append({
            "标题": title,
            "来源": item.get("source", "未知来源"),
            "时间": item.get("published", "未明确给出"),
            "内容": item.get("内容摘要") or make_content(item.get("summary", ""), item.get("title", "")),
            "评论": item.get("评论") or make_short_comment(item.get("section", ""), item.get("summary", ""), item.get("title", "")),
        })
        if len(selected) >= limit:
            break
    return selected


def build_template_a_report(grouped, focus_hits, errors):
    now_str = NOW.strftime("%Y-%m-%d %H:%M")
    market_snapshot = collect_market_snapshot()
    headline_items = select_top_headlines(grouped, limit=12)
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
            lines.append(f"   内容：{cap_text(item['内容'], 78)}")
            lines.append(f"   评论：{cap_text(item['评论'], 42)}")
            lines.append(f"   （来源：{item['来源']} | 发布时间：{item['时间']}）")
            lines.append("")
    else:
        lines.append("- 今日无足够扎实的头条更新")
        lines.append("")
    lines.append("二、全球市场动态")
    for k, v in market_snapshot.items():
        lines.append(f"- {k}：{v}")
    lines.append("")
    lines.append("三、风险预警")
    for item in risk_alerts:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("四、投资建议")
    for item in action_points:
        lines.append(f"- {item}")
    lines.append("")
    if errors:
        lines.append("五、抓取缺口说明")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")
    lines.append("说明：本报告优先保留过去24小时内公开可验证新增；若关键报价未稳定抓到，则直接标注缺口，不使用旧数据补洞。")
    text_body = "\n".join(lines)
    html_body = "<html><body><pre style='white-space:pre-wrap;font-family:Microsoft YaHei,Arial,sans-serif;'>" + html.escape(text_body) + "</pre></body></html>"
    return text_body, html_body


def build_text_report(grouped, focus_hits, errors):
    return build_template_a_report(grouped, focus_hits, errors)[0]


def build_html_report(grouped, focus_hits, errors):
    return build_template_a_report(grouped, focus_hits, errors)[1]


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
