import smtplib
import ssl
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

MARKET_SNAPSHOT = {
    "美股指数": "本轮轻量正式版未稳定直连 NYSE 权威指数页，仅保留财经头条线索，需后续接行情页补点位。",
    "黄金": "本轮未稳定抓到可直接入报的结构化金价，需后续补 Yahoo Finance / Investing 报价页。",
    "布伦特原油": "本轮未稳定抓到可直接入报的布油结构化报价，需后续补 Yahoo Finance / Investing 报价页。",
    "汇率": "本轮未稳定抓到权威结构化汇率快照，需后续补财经报价页。",
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClawFormalIntelV2/1.0"
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


def make_content(summary: str, title: str) -> str:
    base = summary or title or ""
    return cap_text(base, 50) or "今日仅抓到标题级线索，建议继续复核正文。"


def make_conclusion(section: str, summary: str, title: str) -> str:
    base = summary or title or ""
    if section == "宏观新闻":
        text = f"该消息影响地缘风险预期与政策情绪，需关注后续官方表态。{base}"
    elif section == "财经市场":
        text = f"该动态关系市场风险偏好与资产价格方向，宜结合后续报价复核。{base}"
    else:
        text = f"该消息反映科技与产业趋势变化，可跟踪平台与产品落地节奏。{base}"
    return cap_text(text, 40) or "需继续跟踪后续更新。"


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
            key = (item.get("title"), item.get("source"))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)
        focus_hits[topic] = dedup[:4]
    return grouped, focus_hits, errors


def html_escape(s: str) -> str:
    return html.escape(s or "")


def render_news_card(item):
    title = html_escape(item.get("title") or "无标题")
    source = html_escape(item.get("source") or "未知来源")
    published = html_escape(item.get("published") or "未明确给出")
    content = html_escape(item.get("内容摘要") or "")
    conclusion = html_escape(item.get("结论") or "")
    link = html_escape(item.get("link") or "")
    return f"""
    <div style='margin-bottom:18px;padding:14px 16px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;'>
      <div style='font-size:17px;font-weight:700;color:#111827;margin-bottom:8px;'><a href='{link}' style='color:#111827;text-decoration:none;'>{title}</a></div>
      <div style='font-size:13px;color:#6b7280;margin-bottom:8px;'>（来源：{source} | 发布时间：{published}）</div>
      <div style='font-size:14px;color:#1f2937;line-height:1.8;'><b>内容摘要：</b>{content}</div>
      <div style='font-size:14px;color:#7c2d12;line-height:1.8;margin-top:6px;'><b>结论：</b>{conclusion}</div>
    </div>
    """


def render_focus_section(title, items):
    if not items:
        return f"<div style='margin-bottom:16px;'><h4 style='margin:0 0 8px 0;color:#111827;'>{html_escape(title)}</h4><p style='margin:0;color:#6b7280;'>过去24小时未抓到足够扎实的新条目。</p></div>"
    cards = "".join(render_news_card(item) for item in items)
    return f"<div style='margin-bottom:18px;'><h4 style='margin:0 0 10px 0;color:#111827;'>{html_escape(title)}</h4>{cards}</div>"


def build_html_report(grouped, focus_hits, errors):
    now_str = NOW.strftime("%Y-%m-%d %H:%M")
    total = sum(len(v) for v in grouped.values())
    html_parts = [
        "<html><body style='margin:0;padding:0;background:#f3f4f6;font-family:Arial,Microsoft YaHei,sans-serif;'>",
        "<div style='max-width:980px;margin:0 auto;padding:24px;'>",
        "<div style='background:#111827;color:#fff;padding:24px 28px;border-radius:14px 14px 0 0;'>",
        f"<div style='font-size:30px;font-weight:800;'>全球综合情报报告</div>",
        f"<div style='margin-top:8px;font-size:14px;color:#d1d5db;'>报告时间：{html_escape(now_str)} | 时间窗口：过去 24 小时</div>",
        "</div>",
        "<div style='background:#fff;padding:24px 28px;border-radius:0 0 14px 14px;'>",
        "<h3 style='margin-top:0;color:#111827;'>一、执行摘要</h3>",
        f"<ul style='color:#1f2937;line-height:1.8;'><li>本轮共纳入 <b>{total}</b> 条过去24小时内的公开资讯。</li><li>重点盯梢：加沙/以色列/哈马斯、乌克兰/俄罗斯、美中贸易/关税/商业。</li><li>对未抓到的权威实时报价，明确标注缺口，不用旧数据硬补。</li></ul>",
        "<h3 style='color:#111827;'>二、专项聚焦</h3>",
        render_focus_section("加沙 / 以色列 / 哈马斯", focus_hits["加沙/以色列/哈马斯"]),
        render_focus_section("乌克兰 / 俄罗斯", focus_hits["乌克兰/俄罗斯"]),
        render_focus_section("美中贸易 / 关税 / 商业", focus_hits["美中贸易/关税/商业"]),
        "<h3 style='color:#111827;'>三、宏观新闻</h3>",
    ]

    if grouped["宏观新闻"]:
        html_parts.append("".join(render_news_card(item) for item in grouped["宏观新闻"]))
    else:
        html_parts.append("<p style='color:#6b7280;'>过去24小时未抓到足够扎实的宏观新闻更新。</p>")

    html_parts.append("<h3 style='color:#111827;'>四、财经市场</h3>")
    if grouped["财经市场"]:
        html_parts.append("".join(render_news_card(item) for item in grouped["财经市场"]))
    else:
        html_parts.append("<p style='color:#6b7280;'>过去24小时未抓到足够扎实的财经市场更新。</p>")

    html_parts.append("<h3 style='color:#111827;'>五、科技产业</h3>")
    if grouped["科技产业"]:
        html_parts.append("".join(render_news_card(item) for item in grouped["科技产业"]))
    else:
        html_parts.append("<p style='color:#6b7280;'>过去24小时未抓到足够扎实的科技产业更新。</p>")

    html_parts.append("<h3 style='color:#111827;'>六、权威报价补抓状态</h3><ul style='color:#1f2937;line-height:1.9;'>")
    for k, v in MARKET_SNAPSHOT.items():
        html_parts.append(f"<li><b>{html_escape(k)}：</b>{html_escape(v)}</li>")
    html_parts.append("</ul>")

    html_parts.append("<h3 style='color:#111827;'>七、异常与缺口</h3><ul style='color:#1f2937;line-height:1.9;'>")
    if errors:
        for err in errors:
            html_parts.append(f"<li>{html_escape(err)}</li>")
    else:
        html_parts.append("<li>本轮未记录明显抓取异常。</li>")
    html_parts.append("</ul>")

    html_parts.append("<div style='margin-top:28px;padding:16px;background:#fff7ed;border:1px solid #fdba74;border-radius:10px;color:#7c2d12;'>")
    html_parts.append("<b>反幻想说明：</b> 本报告只保留过去24小时内能从公开 feed 解析出的条目；对未抓到的官方发言、交易所点位、黄金、布伦特和汇率，不做虚构补写。")
    html_parts.append("</div>")
    html_parts.append("</div></div></body></html>")
    return "".join(html_parts)


def build_text_report(grouped, focus_hits, errors):
    now_str = NOW.strftime("%Y-%m-%d %H:%M")
    total = sum(len(v) for v in grouped.values())
    lines = [
        f"全球综合情报报告 - {now_str}",
        f"报告时间：{now_str}",
        f"本轮共纳入 {total} 条过去24小时内的公开资讯。",
        "重点盯梢：加沙/以色列/哈马斯、乌克兰/俄罗斯、美中贸易/关税/商业。",
        "抓不到就明确写缺口，不用旧数据硬补。",
        "",
        "一、专项聚焦",
    ]

    focus_map = [
        ("加沙 / 以色列 / 哈马斯", focus_hits["加沙/以色列/哈马斯"]),
        ("乌克兰 / 俄罗斯", focus_hits["乌克兰/俄罗斯"]),
        ("美中贸易 / 关税 / 商业", focus_hits["美中贸易/关税/商业"]),
    ]
    for title, items in focus_map:
        lines.append(f"【{title}】")
        if not items:
            lines.append("- 过去24小时未抓到足够扎实的新条目。")
        else:
            for item in items[:3]:
                lines.append(f"- {item.get('title', '无标题')}（来源：{item.get('source', '未知来源')} | 发布时间：{item.get('published', '未明确给出')}）")
                lines.append(f"  摘要：{item.get('内容摘要', '今日仅抓到标题级线索，建议继续复核正文。')}")
                lines.append(f"  结论：{item.get('结论', '需继续跟踪后续更新。')}")
        lines.append("")

    section_titles = [("二、宏观新闻", "宏观新闻"), ("三、财经市场", "财经市场"), ("四、科技产业", "科技产业")]
    for section_title, key in section_titles:
        lines.append(section_title)
        if not grouped[key]:
            lines.append("- 过去24小时未抓到足够扎实的新条目。")
        else:
            for item in grouped[key][:5]:
                lines.append(f"- {item.get('title', '无标题')}（来源：{item.get('source', '未知来源')} | 发布时间：{item.get('published', '未明确给出')}）")
                lines.append(f"  内容摘要：{item.get('内容摘要', '今日仅抓到标题级线索，建议继续复核正文。')}")
                lines.append(f"  结论：{item.get('结论', '需继续跟踪后续更新。')}")
        lines.append("")

    lines.append("五、权威报价补抓状态")
    for k, v in MARKET_SNAPSHOT.items():
        lines.append(f"- {k}：{v}")
    lines.append("")

    lines.append("六、异常与缺口")
    if errors:
        for err in errors:
            lines.append(f"- {err}")
    else:
        lines.append("- 本轮未记录明显抓取异常。")
    lines.append("")
    lines.append("说明：本报告只保留过去24小时内能从公开 feed 解析出的条目；对未抓到的官方发言、交易所点位、黄金、布伦特和汇率，不做虚构补写。")
    return "\n".join(lines)


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
    grouped, focus_hits, errors = collect_news()
    subject = f"全球综合情报报告 - {NOW.strftime('%Y-%m-%d %H:%M')}"
    text_body = build_text_report(grouped, focus_hits, errors)
    html_body = build_html_report(grouped, focus_hits, errors)
    send_email(subject, text_body, html_body)
    print("FORMAL_REPORT_V2_EMAIL_SENT_OK")


if __name__ == "__main__":
    main()
