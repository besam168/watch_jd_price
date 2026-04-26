import argparse
import json
import os
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime
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


def current_trade_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


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
    subprocess.run(cmd, cwd=str(WORKSPACE), env=env, check=True, capture_output=True, text=True)
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
            f"- 结论：{row.get('decision', 'N/A')}",
            f"- 中文摘要：{row.get('summary_zh') or '暂无摘要'}",
        ]
        reasons = row.get("key_reasons") or []
        if reasons:
            lines.append("- 核心依据：")
            lines += [f"  • {x}" for x in reasons[:3]]
        else:
            lines.append("- 核心依据：暂未稳定提炼到中文依据")
        risks = row.get("risks") or []
        if risks:
            lines.append("- 主要风险：")
            lines += [f"  • {x}" for x in risks[:2]]
        else:
            lines.append("- 主要风险：暂未稳定提炼到中文风险")
        lines += ["",]
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
            f"- 结论：**{row.get('decision', 'N/A')}**",
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
        reasons = row.get("key_reasons") or []
        if reasons:
            lines += [f"- {x}" for x in reasons[:4]]
        else:
            lines.append("- 暂未稳定提炼到核心依据")
        lines += ["", "### 主要风险", ""]
        risks = row.get("risks") or []
        if risks:
            lines += [f"- {x}" for x in risks[:3]]
        else:
            lines.append("- 暂未稳定提炼到主要风险")
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
