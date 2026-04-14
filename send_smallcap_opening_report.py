from __future__ import annotations

import json
import smtplib
import ssl
from datetime import datetime
from email.header import Header
from email.message import EmailMessage
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PYTHON = Path(r"C:\Users\besam\AppData\Local\Programs\Python\Python312\python.exe")
PLUGIN = ROOT / "skills" / "a-share-live-smallcap" / "scripts" / "live_smallcap.py"
REPORT_DIR = ROOT / "reports" / "smallcap_mailer"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SENDER = "910633260@qq.com"
AUTH_CODE = "sghqeeeeyuzjbcbb"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
RECEIVERS = ["besam168168@gmail.com", "758622673@qq.com"]


def run_plugin() -> dict:
    json_path = REPORT_DIR / "latest_smallcap.json"
    cmd = [
        str(PYTHON),
        str(PLUGIN),
        "--json",
        "--output-json",
        str(json_path),
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "插件运行失败\n"
            f"rc={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    if not json_path.exists():
        raise FileNotFoundError(f"未生成结果文件: {json_path}")
    return json.loads(json_path.read_text(encoding="utf-8"))


def fmt_item(item: dict) -> str:
    if not item:
        return "- 无"
    name = item.get("name", "-")
    code = item.get("code", "-")
    change_pct = item.get("change_pct", "-")
    amount_yi = item.get("amount_yi", "-")
    turnover = item.get("turnover") or item.get("turnover_ratio_effective") or item.get("turnover_ratio") or "-"
    conviction = item.get("conviction", "-")
    return f"- {name} {code} | 涨幅 {change_pct}% | 成交额 {amount_yi}亿 | 换手 {turnover} | 信号 {conviction}"


def fmt_item_from_full(item: dict) -> str:
    if not item:
        return "- 无"
    name = item.get("name", "-")
    code = item.get("code", "-")
    change_pct = item.get("change_pct", "-")
    amount_yi = item.get("amount_yi", "-")
    turnover = item.get("turnover_ratio_effective") or item.get("turnover_ratio") or item.get("turnover_ratio_est") or "-"
    conviction = item.get("conviction", "-")
    return f"- {name} {code} | 涨幅 {change_pct}% | 成交额 {amount_yi}亿 | 换手 {turnover} | 信号 {conviction}"


def build_text_report(payload: dict) -> str:
    generated_at = payload.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    source = payload.get("market_scan_source", "unknown")
    summary = (payload.get("chinese_summary") or {}).get("overall", "暂无总结")
    role_board = payload.get("role_board") or {}
    true_leaders = payload.get("true_leaders") or []
    strong_followers = payload.get("strong_followers") or []
    pseudo_strong = payload.get("pseudo_strong") or []
    watchlist = payload.get("watchlist") or []

    lines = []
    lines.append(f"A股中小盘强势早盘筛选 - {generated_at}")
    lines.append("")
    lines.append(f"扫描来源：{source}")
    lines.append(f"一句话结论：{summary}")
    lines.append("")
    lines.append("一、真龙头")
    if true_leaders:
        for item in true_leaders[:5]:
            lines.append(fmt_item_from_full(item))
    else:
        lines.append("- 今日暂无明确真龙头")

    lines.append("")
    lines.append("二、强跟随")
    if strong_followers:
        for item in strong_followers[:6]:
            lines.append(fmt_item_from_full(item))
    else:
        lines.append("- 今日暂无强跟随")

    lines.append("")
    lines.append("三、伪强观察")
    if pseudo_strong:
        for item in pseudo_strong[:6]:
            lines.append(fmt_item_from_full(item))
    else:
        lines.append("- 今日暂无明显伪强票")

    lines.append("")
    lines.append("四、重点盯盘名单")
    if watchlist:
        for item in watchlist[:5]:
            lines.append(fmt_item_from_full(item))
    else:
        lines.append("- 今日暂无重点盯盘名单")

    lines.append("")
    lines.append("五、角色看板")
    dragon_one = role_board.get("dragon_one")
    dragon_two = role_board.get("dragon_two")
    lines.append("龙一：")
    lines.append(fmt_item(dragon_one))
    lines.append("龙二：")
    lines.append(fmt_item(dragon_two))

    followers = role_board.get("followers") or []
    lines.append("跟随：")
    if followers:
        for item in followers:
            lines.append(fmt_item(item))
    else:
        lines.append("- 无")

    observe = role_board.get("observe") or []
    lines.append("观察：")
    if observe:
        for item in observe:
            lines.append(fmt_item(item))
    else:
        lines.append("- 无")

    lines.append("")
    lines.append("说明：本邮件为每日 09:35 自动执行结果，使用 Python312 固定环境运行。")
    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECEIVERS)
    msg["Subject"] = subject
    msg.set_content(body, subtype="plain", charset="utf-8")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
        server.login(SENDER, AUTH_CODE)
        server.send_message(msg)


def main() -> int:
    payload = run_plugin()
    body = build_text_report(payload)
    stamp = datetime.now().strftime("%Y-%m-%d")
    subject = f"【沈万三】A股中小盘强势早盘筛选 - {stamp}"

    txt_path = REPORT_DIR / "latest_smallcap_mail.txt"
    txt_path.write_text(body, encoding="utf-8")

    send_email(subject, body)
    print("SMALLCAP_MAIL_OK")
    print(txt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
