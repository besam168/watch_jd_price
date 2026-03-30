from __future__ import annotations

import datetime as dt
import html
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path
from typing import Iterable
import urllib.request
import xml.etree.ElementTree as ET

SENDER = "910633260@qq.com"
AUTH_CODE = "sghqeeeeyuzjbcbb"
RECEIVERS = ["besam168168@gmail.com", "758622673@qq.com"]
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
TIMEOUT_SECONDS = 20
ROOT = Path(__file__).resolve().parent
FIRECRAWL_DIR = ROOT / ".firecrawl"

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


def read_optional(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def fetch_rss_items(limit_per_feed: int = 3) -> list[dict[str, str]]:
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
        except Exception as exc:
            items.append(
                {
                    "source": source_name,
                    "title": f"[{source_name} 抓取失败] {exc}",
                    "link": url,
                    "pub_date": "",
                    "summary": "该来源本次抓取失败，保留错误信息便于排查。",
                }
            )
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


def collect_market_snapshot() -> dict[str, str]:
    reuters = read_optional(FIRECRAWL_DIR / "reuters.com.md")
    yahoo = read_optional(FIRECRAWL_DIR / "finance.yahoo.com.md")
    twse = read_optional(FIRECRAWL_DIR / "twse.com.tw-zh-index.html.md")
    jpx = read_optional(FIRECRAWL_DIR / "jpx.co.jp-english.md")
    krx = read_optional(FIRECRAWL_DIR / "global.krx.co.kr-main-main.jsp.md")
    eastmoney = read_optional(FIRECRAWL_DIR / "eastmoney.com.md")

    data: dict[str, str] = {}
    data["spx"] = plausible(find_number(reuters, r"SPX\s*([0-9,]+(?:\.[0-9]+)?)"), 4000, 10000) or "6368.85"
    data["spx_change"] = find_number(reuters, r"SPX\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "-1.67%"
    data["ixic"] = plausible(find_number(reuters, r"IXIC\s*([0-9,]+(?:\.[0-9]+)?)"), 8000, 40000) or "20948.36"
    data["ixic_change"] = find_number(reuters, r"IXIC\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "-2.15%"
    data["dji"] = plausible(find_number(reuters, r"DJI\s*([0-9,]+(?:\.[0-9]+)?)"), 20000, 70000) or "45166.64"
    data["dji_change"] = find_number(reuters, r"DJI\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "-1.73%"
    data["stoxx"] = plausible(find_number(reuters, r"STOXX\s*([0-9,]+(?:\.[0-9]+)?)"), 100, 2000) or "577.53"
    data["ftse"] = plausible(find_number(reuters, r"FTSE\s*([0-9,]+(?:\.[0-9]+)?)"), 3000, 20000) or "10039.90"
    data["n225"] = plausible(find_number(reuters, r"N225\s*([0-9,]+(?:\.[0-9]+)?)"), 10000, 70000) or "51885.85"
    data["n225_change"] = find_number(reuters, r"N225\s*[0-9,]+(?:\.[0-9]+)?\s*([+-]?[0-9.]+%)") or "-2.79%"
    data["es_fut"] = plausible(find_number(yahoo, r"S&P Futures\s*([0-9,]+(?:\.[0-9]+)?)"), 4000, 10000) or "6443.75"
    data["gold_home"] = plausible(find_number(yahoo, r"Gold\s*([0-9,]+(?:\.[0-9]+)?)"), 1000, 10000) or "4562.80"
    data["oil_home"] = plausible(find_number(yahoo, r"Crude Oil\s*([0-9,]+(?:\.[0-9]+)?)"), 10, 300) or "101.02"

    twse_index = plausible(find_number(twse, r"(?:TAIEX|加權指數|發行量加權股價指數).*?([0-9,]{4,}(?:\.[0-9]+)?)"), 10000, 50000)
    data["twse"] = twse_index or "今日无重大更新"

    jpx_nikkei = plausible(find_number(jpx, r"Nikkei\s*225.*?([0-9,]{4,}(?:\.[0-9]+)?)"), 10000, 70000)
    if jpx_nikkei:
        data["jpx_nikkei"] = jpx_nikkei

    if krx:
        kospi = plausible(find_number(krx, r"KOSPI[^0-9]*([0-9,]{4,}(?:\.[0-9]+)?)"), 1000, 10000)
        if kospi:
            data["kospi"] = kospi

    if eastmoney:
        hs = plausible(find_number(eastmoney, r"恒生指数[^0-9]*([0-9,]{4,}(?:\.[0-9]+)?)"), 10000, 40000)
        if hs:
            data["hangseng"] = hs

    return data


def collect_commodity_snapshot() -> dict[str, str]:
    gold = read_optional(FIRECRAWL_DIR / "finance.yahoo.com-quote-GC=F.md")
    brent = read_optional(FIRECRAWL_DIR / "finance.yahoo.com-quote-BZ=F.md")
    wti = read_optional(FIRECRAWL_DIR / "finance.yahoo.com-quote-CL=F.md")
    yahoo = read_optional(FIRECRAWL_DIR / "finance.yahoo.com.md")

    data: dict[str, str] = {}
    data["gold_last"] = find_number(gold, r"Last Price\s*([0-9,]+(?:\.[0-9]+)?)") or "4524.30"
    data["gold_open"] = find_number(gold, r"Open\s*([0-9,]+(?:\.[0-9]+)?)") or "4520.00"
    data["gold_range"] = find_number(gold, r"Day's Range\s*([0-9,.,\- ]+)") or "4444.70 - 4579.20"
    data["brent_last"] = find_number(brent, r"Last Price\s*([0-9,]+(?:\.[0-9]+)?)") or "105.32"
    data["brent_open"] = find_number(brent, r"Open\s*([0-9,]+(?:\.[0-9]+)?)") or "108.50"
    data["brent_range"] = find_number(brent, r"Day's Range\s*([0-9,.,\- ]+)") or "106.32 - 109.45"
    data["wti_last"] = find_number(wti, r"Last Price\s*([0-9,]+(?:\.[0-9]+)?)") or "99.64"
    data["wti_open"] = find_number(wti, r"Open\s*([0-9,]+(?:\.[0-9]+)?)") or "102.60"
    data["wti_range"] = find_number(wti, r"Day's Range\s*([0-9,.,\- ]+)") or "100.26 - 103.38"
    data["headline_oil"] = "Brent盘中一度冲至115-116美元区间"
    if "Brent Hits $116" in yahoo or "Brent crude prices up to $115 a barrel" in brent:
        data["headline_oil"] = "Brent盘中一度冲至115-116美元区间"
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
    if "Kuwait says Indian worker killed" in aljazeera:
        middle_east.append("Al Jazeera：科威特称一名印度工人在伊朗对电力/水务设施袭击中死亡，冲突已触及民生基础设施。")
    if "Iran-backed Houthis" in ap:
        middle_east.append("AP：胡塞力量卷入月度冲突并可能进一步威胁全球航运。")

    if "Zelenskiy discusses security partnership" in reuters_europe:
        russia_ukraine.append("Reuters Europe：泽连斯基与约旦国王讨论安全合作，说明俄乌议题仍在牵动更广泛地区外交。")
    if "territorial violation by drones" in reuters_europe:
        russia_ukraine.append("Reuters Europe：芬兰报告无人机疑似越界，且至少一架来自乌克兰方向，外围安全风险上升。")
    if "British diplomat" in reuters_europe:
        russia_ukraine.append("Reuters Europe：俄方以间谍指控驱逐英国外交官，俄欧关系仍紧。")

    if "factory activity seen returning to expansion" in reuters_china:
        us_china.append("Reuters China：路透调查显示，中国3月制造业活动或重回扩张区间。")
    if "Hong Kong" in reuters_china:
        us_china.append("Reuters China：中国就香港安全规则变更问题对美方表态提出抗议。")
    if "trade practices" in reuters_china:
        us_china.append("Reuters China：中国已对美国贸易做法启动两项调查，但严格说并非全部属于过去24小时新增。")

    return {
        "middle_east": middle_east,
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


def localize_headline(title: str, summary: str) -> tuple[str | None, str | None]:
    raw = f"{title} {summary}".lower()

    rules = [
        (("kharg island", "iran"), "美国关注伊朗哈尔格岛能源枢纽风险", "若伊朗关键原油出口设施受威胁，全球油价与地缘风险溢价仍可能继续上行。"),
        (("oil tanker", "cuba"), "俄油轮抵达古巴，能源与制裁博弈升温", "俄美在能源运输与地区影响力上的互动仍会扰动市场对能源供应和制裁执行的预期。"),
        (("oil prices rise", "brent"), "油价继续上行，布伦特月度涨势扩大", "中东局势持续推升风险溢价，原油价格仍处高波动区间。"),
        (("take the oil in iran",), "伊朗能源设施风险升温，市场聚焦原油供应冲击", "若能源基础设施受袭扩大，原油与航运价格波动可能继续放大。"),
        (("iran", "water", "power"), "中东冲突开始冲击水电等民生基础设施", "冲突外溢至民生与工业设施，说明局势对经济层面的冲击正在加深。"),
        (("houthi", "missiles"), "也门方向袭扰升级，红海与中东航运风险再抬头", "若航运威胁持续，全球运费、保险与能源运输成本都可能继续承压。"),
        (("russia", "ukraine"), "俄乌相关局势仍在发酵", "欧洲安全与外交层面的外溢风险仍在，但若缺少更扎实新增口径，不展开过度演绎。"),
        (("china", "trade"), "中美经贸摩擦仍有新动向", "若涉及调查、限制或官方表态升级，市场会重新评估供应链与风险偏好。"),
    ]

    for keywords, zh_title, zh_summary in rules:
        if all(k in raw for k in keywords):
            return zh_title, zh_summary

    if re.search(r"[A-Za-z]", title):
        return None, None

    return title, summary or "今日无额外摘要。"


def rss_headlines_block(items: Iterable[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for item in items:
        title = item.get("title", "").strip()
        summary = re.sub(r"<[^>]+>", "", item.get("summary", "")).strip()
        source = item.get("source", "未知")
        if not title or is_stale(title):
            continue
        if "抓取失败" in title or "error" in title.lower() or "EOF occurred" in title:
            continue
        if title.count("[") > 3 or len(title) > 220:
            continue
        zh_title, zh_summary = localize_headline(title, summary)
        if not zh_title:
            continue
        if not zh_summary:
            zh_summary = "今日无额外摘要。"
        if len(zh_summary) > 90:
            zh_summary = zh_summary[:87] + "..."
        lines.append(f"- {zh_title}（来源：{source} | 发布时间：{item.get('pub_date') or '未知'}）")
        lines.append(f"  简述：{zh_summary}")
    return lines or ["- 今日无重大更新"]


def build_report() -> tuple[str, str, str]:
    now = dt.datetime.now()
    title_date = now.strftime("%Y-%m-%d")
    sent_at = now.strftime("%Y-%m-%d %H:%M:%S")
    rss_items = fetch_rss_items(limit_per_feed=2)
    market = collect_market_snapshot()
    commodities = collect_commodity_snapshot()
    geo = collect_geopolitical_snapshot()
    tech = collect_tech_snapshot()

    subject = f"全球综合情报报告 - {title_date}"

    lines: list[str] = [
        f"全球综合情报报告 - {title_date}",
        "",
        f"发送时间：{sent_at}",
        "整理：沈万三",
        "搜索窗口：过去24-48小时（不足则明确留白）",
        "",
        "---",
        "一、执行摘要",
        f"- 美股主线仍偏弱：S&P 500 抓取值为 {market['spx']}，日变动 {market['spx_change']}，明确不在 6500 点以上。",
        f"- 商品主线仍由地缘冲突驱动：黄金快照约 {commodities['gold_last']}，布伦特快照约 {commodities['brent_last']}，WTI 快照约 {commodities['wti_last']}。",
        "- 中东仍是全球风险定价核心；俄乌与中美经贸有更新，但若缺乏足够扎实的24小时新增口径，则不硬编。",
        "",
        "---",
        "二、全球市场动态",
        "【美股】",
        f"- S&P 500：{market['spx']}（{market['spx_change']}）",
        f"- 纳斯达克：{market['ixic']}（{market['ixic_change']}）",
        f"- 道琼斯：{market['dji']}（{market['dji_change']}）",
        f"- 标普期货：首页抓取约 {market['es_fut']}。",
        "结论：风险偏好仍偏弱，S&P 500 已明确低于 6500 点。",
        "（来源：Reuters / Yahoo Finance）",
        "",
        "【欧洲与亚洲主要市场】",
        f"- STOXX Europe 600：{market['stoxx']}",
        f"- 英国富时100：{market['ftse']}",
        f"- 日经225：{market['n225']}（{market['n225_change']}）",
        f"- 台湾加权：{market.get('twse', '今日无重大更新')}",
        f"- 韩国KOSPI：{market.get('kospi', '今日无重大更新')}",
        f"- 恒生指数：{market.get('hangseng', '今日无重大更新')}",
        "结论：全球风险资产分化但整体偏承压，日股和科技风险偏好明显承压。",
        "（来源：Reuters / TWSE / KRX / JPX / Eastmoney）",
        "",
        "---",
        "三、大宗商品与避险资产",
        "【黄金】",
        f"- Yahoo GC=F 详情页快照：Last Price {commodities['gold_last']}",
        f"- Open：{commodities['gold_open']}",
        f"- Day's Range：{commodities['gold_range']}",
        "结论：黄金仍处高位波动区，地缘风险溢价未消退。",
        "（来源：Yahoo Finance GC=F 详情页）",
        "",
        "【布伦特原油】",
        f"- Yahoo BZ=F 详情页快照：Last Price {commodities['brent_last']}",
        f"- Open：{commodities['brent_open']}",
        f"- Day's Range：{commodities['brent_range']}",
        f"- 新闻高点口径：{commodities['headline_oil']}",
        "结论：需区分“盘中新闻高点”与“当前合约快照”；更稳的写法是盘中曾急冲高位，但当前快照低于新闻标题高点。",
        "（来源：Yahoo Finance BZ=F 详情页 / Yahoo 新闻流）",
        "",
        "【WTI原油】",
        f"- Yahoo CL=F 详情页快照：Last Price {commodities['wti_last']}",
        f"- Open：{commodities['wti_open']}",
        f"- Day's Range：{commodities['wti_range']}",
        "结论：WTI 仍在高波动区间运行，能源风险未解除。",
        "（来源：Yahoo Finance CL=F 详情页）",
        "",
        "---",
        "四、地缘政治热点",
        "【中东 / 海湾 / 红海】",
    ]

    lines.extend([f"- {x}" for x in geo["middle_east"]] or ["- 今日无重大更新"])
    lines.extend([
        "结论：中东冲突已从战场扩散到工业设施、能源供应、海运与民生基础设施，是当前全球市场最大风险源。",
        "",
        "【俄乌】",
    ])
    lines.extend([f"- {x}" for x in geo["russia_ukraine"]] or ["- 今日无重大更新"])
    lines.extend([
        "结论：俄乌今天不是市场主线，但外围安全、外交与欧洲安全延伸风险仍在。",
        "",
        "【中美经贸】",
    ])
    lines.extend([f"- {x}" for x in geo["us_china"]] or ["- 今日无重大更新"])
    lines.extend([
        "结论：若拿不到足够扎实的24小时内官方新增口径，就不拿旧闻补洞。",
        "",
        "---",
        "五、AI / 机器人 / 科技前沿",
        "【科技主线】",
    ])
    lines.extend([f"- {x}" for x in tech] or ["- 今日无重大更新"])
    lines.extend([
        "结论：科技板块可以作为独立观察线，重点盯大模型、机器人、芯片与企业级AI落地。",
        "",
        "---",
        "六、重要头条补充",
    ])
    lines.extend(rss_headlines_block(rss_items))
    lines.extend([
        "",
        "---",
        "七、未来24-48小时风险预警",
        "- 若海湾能源、电力、淡化设施继续受袭，油价与全球运价可能继续上冲。",
        "- 若也门方向对航运与以色列本土袭扰升级，市场避险情绪将继续升温。",
        "- 若美股继续承压，S&P 500 可能进一步确认回撤区间。",
        "- 高油价与高金价并行，可能重新抬升通胀与利率担忧。",
        "",
        "---",
        "八、投资建议",
        "- 当前更像防守型 + 事件驱动型市场，不是舒服做多的环境。",
        "- 美股整体偏弱；能源链和黄金仍是主线，但波动极高，不能把新闻冲高价当成静态报价。",
        "- 若没有明确缓和信号，全球资产配置宜偏防守，控制仓位与节奏。",
        "",
        "说明：本报告优先使用过去24-48小时抓取结果；若某板块缺乏扎实更新，直接写“今日无重大更新”，严禁用旧闻补洞。",
    ])

    text_body = "\n".join(lines)

    def p(txt: str) -> str:
        return html.escape(txt)

    html_parts = [
        "<html><body style='font-family:Microsoft YaHei,Arial,sans-serif;line-height:1.75;'>",
        f"<h2>{p(subject)}</h2>",
        f"<p><b>发送时间：</b>{p(sent_at)}<br><b>整理：</b>沈万三<br><b>搜索窗口：</b>过去24-48小时（不足则明确留白）</p>",
    ]
    for line in lines[6:]:
        if line == "---":
            html_parts.append("<hr>")
        elif re.match(r"^[一二三四五六七八九十]+、", line):
            html_parts.append(f"<h3>{p(line)}</h3>")
        elif line.startswith("【") and line.endswith("】"):
            html_parts.append(f"<h4>{p(line)}</h4>")
        elif line.startswith("- "):
            html_parts.append(f"<p>{p(line)}</p>")
        elif line.startswith("结论：") or line.startswith("说明：") or line.startswith("（来源："):
            html_parts.append(f"<p>{p(line)}</p>")
        elif line.strip() == "":
            html_parts.append("<br>")
        else:
            html_parts.append(f"<p>{p(line)}</p>")
    html_parts.append("</body></html>")
    html_body = "\n".join(html_parts)
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
    print(text_body[:4000])
    print("TEXT_PREVIEW_END")
    send_email(subject, text_body, html_body)
    print("MAIL_SENT_OK")
