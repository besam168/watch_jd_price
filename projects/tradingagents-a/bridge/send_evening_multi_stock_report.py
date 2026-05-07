import argparse
import json
import os
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

WORKSPACE = Path(r"C:\Users\besam\.openclaw\workspace")
PROJECT = WORKSPACE / "projects" / "tradingagents-a"
BRIDGE = PROJECT / "bridge"
REPO = PROJECT / "repo"
PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
RUNNER = BRIDGE / "run_tradingagents_bridge.py"
OUTDIR = BRIDGE / "outputs"
REPORT_DIR = BRIDGE / "scheduled_reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "910633260@qq.com"
SMTP_PASS = "sghqeeeeyuzjbcbb"
OPENAI_API_KEY = "sk-a9055f399bb3abec29a5c5eb5b75a4947aa70b2bcbccd3f542553b3fa9190a0f"
DEFAULT_PROFILE = "hi_code_gpt54"
CONFIG_PATH = BRIDGE / "evening_multi_stock_config.json"
FALLBACK_DEFAULT_TICKERS = ["TSLA", "AAPL", "RXRX"]
YFINANCE_SYMBOLS = {
    "TSLA": "TSLA",
    "AAPL": "AAPL",
    "RXRX": "RXRX",
    "NVDA": "NVDA",
    "MSFT": "MSFT",
    "AMZN": "AMZN",
    "META": "META",
}


def current_trade_date() -> str:
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:
        back_days = weekday - 4
        now = now - timedelta(days=back_days)
    return now.strftime("%Y-%m-%d")


def load_config() -> dict:
    cfg = {}
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg.setdefault("defaultTickers", FALLBACK_DEFAULT_TICKERS)
    cfg.setdefault("maxTickers", 3)
    trade_date = str(cfg.get("tradeDate") or "").strip()
    if not trade_date or trade_date == "2024-05-10":
        trade_date = current_trade_date()
    cfg["tradeDate"] = trade_date
    cfg.setdefault("recipients", ["besam168168@gmail.com", "758622673@qq.com"])
    cfg.setdefault("subjectPrefix", "晚间热点多票合集报告")
    return cfg


def run_ticker(ticker: str, trade_date: str) -> dict:
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = OPENAI_API_KEY
    cmd = [str(PYTHON), str(RUNNER), "--ticker", ticker, "--date", trade_date, "--profile", DEFAULT_PROFILE]
    try:
        subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired as e:
        return build_timeout_fallback(ticker, int(float(e.timeout) * 1000), trade_date)
    except subprocess.CalledProcessError as e:
        status = {}
        result = {}
        if (OUTDIR / "latest-status.json").exists():
            status = json.loads((OUTDIR / "latest-status.json").read_text(encoding="utf-8"))
        if (OUTDIR / "latest-result.json").exists():
            result = json.loads((OUTDIR / "latest-result.json").read_text(encoding="utf-8"))
        error_msg = (status.get("error") or result.get("error") or e.stderr or e.stdout or str(e)).strip()
        fallback = build_market_data_fallback(ticker, trade_date)
        if fallback:
            fallback["summary_zh"] = f"深度分析失败，已自动降级为轻量行情摘要：{fallback['summary_zh']}"
            fallback["key_reasons"].insert(0, f"底层 TradingAgents bridge 返回非零退出码：{error_msg[:120]}")
            fallback["risks"].append("当前深度分析链路稳定性不足，已自动回退为轻量结论")
            return fallback
        return {
            "ticker": ticker,
            "decision": "ERROR",
            "summary_zh": f"运行失败：{error_msg}",
            "key_reasons": ["底层 TradingAgents bridge 返回非零退出码，单票分析未正常完成"],
            "risks": ["当前桥接链路存在稳定性问题，批量晚报可能被个别标的拖垮"],
            "ok": False,
            "duration_ms": status.get("duration_ms"),
            "profile": result.get("profile") or status.get("profile") or DEFAULT_PROFILE,
            "provider": result.get("provider") or status.get("provider") or "openai",
            "model": result.get("model") or status.get("model") or "gpt-5.4",
        }
    result = json.loads((OUTDIR / "latest-result.json").read_text(encoding="utf-8"))
    status = json.loads((OUTDIR / "latest-status.json").read_text(encoding="utf-8"))
    return {
        "ticker": ticker,
        "decision": result.get("decision"),
        "summary_zh": result.get("summary_zh"),
        "key_reasons": result.get("key_reasons") or [],
        "risks": result.get("risks") or [],
        "ok": result.get("ok"),
        "duration_ms": status.get("duration_ms"),
        "profile": result.get("profile"),
        "provider": result.get("provider"),
        "model": result.get("model"),
    }


def build_timeout_fallback(ticker: str, timeout_ms: int, trade_date: str) -> dict:
    fallback = build_market_data_fallback(ticker, trade_date)
    if fallback:
        fallback["summary_zh"] = f"深度分析超时，已自动降级为轻量行情摘要：{fallback['summary_zh']}"
        fallback["key_reasons"].insert(0, f"单票分析超过 {int(timeout_ms / 1000)} 秒，已跳过重型 agent graph")
        fallback["risks"].append("当前深度分析层存在普遍超时风险，建议把该结论视为轻量版参考")
        return fallback
    return {
        "ticker": ticker,
        "decision": "ERROR",
        "summary_zh": f"运行超时：单票分析超过 {int(timeout_ms / 1000)} 秒，且轻量兜底也未成功生成。",
        "key_reasons": ["底层 agent graph 在拉完行情与指标后长时间阻塞，未及时产出最终结论"],
        "risks": ["当前桥接链路稳定性不足，晚间批量任务容易被单票超时拖住"],
        "ok": False,
        "duration_ms": timeout_ms,
        "profile": DEFAULT_PROFILE,
        "provider": "openai",
        "model": "gpt-5.4",
    }


def build_market_data_fallback(ticker: str, trade_date: str) -> dict | None:
    symbol = YFINANCE_SYMBOLS.get(ticker.upper(), ticker.upper())
    helper = WORKSPACE / "quick_market_snapshot.py"
    script = (
        "import json, yfinance as yf; "
        f"df=yf.Ticker('{symbol}').history(period='10d'); "
        "assert not df.empty, 'empty_history'; "
        "close=float(df['Close'].iloc[-1]); "
        "prev=float(df['Close'].iloc[-2]) if len(df)>1 else close; "
        "ma5=float(df['Close'].tail(5).mean()); "
        "chg=(close-prev)/prev*100 if prev else 0.0; "
        "trend='UP' if close>=ma5 else 'DOWN'; "
        "print(json.dumps({'close':close,'prev':prev,'ma5':ma5,'change_pct':chg,'trend':trend}, ensure_ascii=False))"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=35,
            check=True,
        )
        payload = json.loads((proc.stdout or "").strip())
    except Exception:
        return None

    close = float(payload.get("close"))
    prev = float(payload.get("prev"))
    ma5 = float(payload.get("ma5"))
    change_pct = float(payload.get("change_pct"))
    trend = str(payload.get("trend") or "FLAT")
    if change_pct >= 2:
        decision = "BUY"
    elif change_pct <= -2:
        decision = "SELL"
    else:
        decision = "HOLD"
    trend_zh = "站上5日均线" if trend == "UP" else "回到5日均线下方"
    direction_zh = "上涨" if change_pct >= 0 else "下跌"
    return {
        "ticker": ticker,
        "decision": decision,
        "summary_zh": f"{ticker} 当日收盘约 {close:.2f} 美元，较前一交易日{direction_zh} {abs(change_pct):.2f}%，当前{trend_zh}。",
        "key_reasons": [
            f"最新收盘价 {close:.2f}，前收 {prev:.2f}，单日涨跌幅 {change_pct:+.2f}%",
            f"5日均线约 {ma5:.2f}，当前价格与短线均线关系为：{trend_zh}",
            f"该结论为轻量兜底，不依赖重型 TradingAgents 推理，可保证批量任务继续输出",
        ],
        "risks": [
            "该结果未包含完整 agent graph 的多角色深度推理，只适合作为降级版晚报参考",
            "若次日仍需高置信结论，建议对白名单个股单独重跑深度分析",
        ],
        "ok": True,
        "duration_ms": 0,
        "profile": f"{DEFAULT_PROFILE}_fallback",
        "provider": "yfinance",
        "model": "lightweight-market-fallback",
    }


def zh_decision(decision: str | None) -> str:
    mapping = {
        "BUY": "偏多",
        "HOLD": "观望",
        "SELL": "偏空",
        "ERROR": "运行失败",
    }
    if not decision:
        return "未给出"
    return mapping.get(str(decision).upper(), str(decision))


def zh_bullets(items: list[str], fallback: str, limit: int) -> list[str]:
    rows = []
    for item in (items or [])[:limit]:
        text = str(item).strip()
        if not text:
            continue
        text = text.replace("Short-term", "短线")
        text = text.replace("Medium-term", "中线")
        text = text.replace("Long-term", "长线")
        text = text.replace("Price", "股价")
        text = text.replace("risk", "风险")
        text = text.replace("support", "支撑")
        text = text.replace("resistance", "压力")
        text = text.replace("rebound", "反弹")
        text = text.replace("downtrend", "下行趋势")
        text = text.replace("bullish", "偏强")
        text = text.replace("bearish", "偏弱")
        text = text.replace("moving average", "均线")
        rows.append(text)
    if not rows:
        return [fallback]
    return rows


def render_email_body(trade_date: str, rows: list[dict]) -> str:
    lines = [
        f"晚间热点多票合集报告（{trade_date}）",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"覆盖标的：{', '.join(r['ticker'] for r in rows)}",
        "",
        "一、总览",
        "- 本邮件为晚间自动汇总版，优先给出中文结论、核心依据、主要风险与关键提示。",
        "- 当前版本先覆盖 3 只默认股票，后续可继续扩展热点池与 HTML 附件样式。",
        "",
    ]
    for idx, row in enumerate(rows, start=1):
        lines += [
            f"二.{idx} {row['ticker']}",
            f"- 结论：{zh_decision(row.get('decision'))}（{row.get('decision', 'N/A')}）",
            f"- 中文摘要：{row.get('summary_zh') or '暂无摘要'}",
        ]
        reasons = zh_bullets(row.get("key_reasons") or [], "暂未稳定提炼到中文依据", 3)
        lines.append("- 核心依据：")
        lines += [f"  • {x}" for x in reasons]
        risks = zh_bullets(row.get("risks") or [], "暂未稳定提炼到中文风险", 2)
        lines.append("- 主要风险：")
        lines += [f"  • {x}" for x in risks]
        lines += [""]
    lines += [
        "三、说明",
        "- 当前分析由 TradingAgents Bridge 自动生成，路由优先走已打通的 OpenAI 兼容链路。",
        "- 邮件正文以中文简报优先，附件保留完整 markdown 报告，便于复盘与转存。",
    ]
    return "\n".join(lines)


def render_markdown(trade_date: str, rows: list[dict]) -> str:
    lines = [
        f"# 每日晚间热点多票合集报告 - {trade_date}",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 覆盖标的：{', '.join(r['ticker'] for r in rows)}",
        "",
        "---",
        "",
    ]
    for idx, row in enumerate(rows, start=1):
        lines += [
            f"## {idx}. {row['ticker']}",
            "",
            f"- 结论：**{zh_decision(row.get('decision'))}**（{row.get('decision', 'N/A')}）",
            f"- 路由：{row.get('provider', 'n/a')}/{row.get('model', 'n/a')} ({row.get('profile', 'n/a')})",
            f"- 耗时：{row.get('duration_ms', 'n/a')} ms",
            "",
            f"### 中文摘要",
            "",
            row.get("summary_zh") or "（暂无摘要）",
            "",
            "### 核心依据",
            "",
        ]
        reasons = zh_bullets(row.get("key_reasons") or [], "暂未稳定提炼到中文依据", 4)
        lines += [f"- {x}" for x in reasons]
        lines += ["", "### 主要风险", ""]
        risks = zh_bullets(row.get("risks") or [], "暂未稳定提炼到中文风险", 3)
        lines += [f"- {x}" for x in risks]
        lines += ["", "---", ""]
    return "\n".join(lines)


def send_mail(subject: str, body_text: str, attachment_path: Path, recipients: list[str]):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg.set_content(body_text)

    data = attachment_path.read_bytes()
    msg.add_attachment(data, maintype="text", subtype="markdown", filename=attachment_path.name)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def main():
    cfg = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=cfg.get("tradeDate") or current_trade_date())
    parser.add_argument("--tickers", default=",".join(cfg.get("defaultTickers", FALLBACK_DEFAULT_TICKERS)))
    args = parser.parse_args()
    if not str(args.date).strip() or str(args.date).strip().upper() == "AUTO":
        args.date = current_trade_date()

    max_tickers = int(cfg.get("maxTickers", 3))
    recipients = cfg.get("recipients") or ["besam168168@gmail.com", "758622673@qq.com"]
    subject_prefix = cfg.get("subjectPrefix", "晚间热点多票合集报告")
    tickers = [x.strip().upper() for x in args.tickers.split(",") if x.strip()]
    rows = []
    for ticker in tickers[:max_tickers]:
        try:
            rows.append(run_ticker(ticker, args.date))
        except Exception as e:
            rows.append({
                "ticker": ticker,
                "decision": "ERROR",
                "summary_zh": f"运行失败：{e}",
                "key_reasons": [],
                "risks": [],
                "ok": False,
                "duration_ms": None,
                "profile": DEFAULT_PROFILE,
                "provider": "openai",
                "model": "gpt-5.4",
            })

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md = render_markdown(args.date, rows)
    body = render_email_body(args.date, rows)
    report_path = REPORT_DIR / f"multi_stock_evening_report_{stamp}.md"
    report_path.write_text(md, encoding="utf-8")

    subject = f"{subject_prefix} - {args.date}"
    send_mail(subject, body, report_path, recipients)
    print(json.dumps({"ok": True, "report": str(report_path), "subject": subject, "tickers": tickers[:max_tickers], "recipients": recipients}, ensure_ascii=False))


if __name__ == "__main__":
    main()
