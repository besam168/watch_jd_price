from __future__ import annotations

import json
import smtplib
import ssl
import sys
import time
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
PYTHON = Path(r"C:\Users\besam\AppData\Local\Programs\Python\Python312\python.exe")
PLUGIN = ROOT / "skills" / "a-share-live-smallcap" / "scripts" / "live_smallcap.py"
REPORT_DIR = ROOT / "reports" / "smallcap_mailer"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "smallcap_opening_mailer.log"
SHARED_POOL_DIR = ROOT / "skills" / "shared_a_share_pool"
sys.path.insert(0, str(SHARED_POOL_DIR.parent))
from shared_a_share_pool.trading_day_guard import guard_non_trading_day

SENDER = "910633260@qq.com"
AUTH_CODE = "sghqeeeeyuzjbcbb"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
RECEIVERS = ["besam168168@gmail.com", "758622673@qq.com"]
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
QQBOT_TARGET = "qqbot:c2c:A79F990232234F712BD31B9E2FF973F6"
QQBOT_CHANNEL = "qqbot"
OPENCLAW_CMD = r"C:\Users\besam\AppData\Roaming\npm\openclaw.ps1"


def log_line(text: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {text}\n")


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
    log_line(f"run_plugin rc={completed.returncode}")
    if completed.stdout.strip():
        log_line(f"plugin_stdout={completed.stdout.strip()[:1000]}")
    if completed.stderr.strip():
        log_line(f"plugin_stderr={completed.stderr.strip()[:1000]}")
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


def build_qq_brief(payload: dict) -> str:
    generated_at = payload.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    summary = (payload.get("chinese_summary") or {}).get("overall", "暂无总结")
    true_leaders = payload.get("true_leaders") or []
    strong_followers = payload.get("strong_followers") or []
    watchlist = payload.get("watchlist") or []

    def short(items: list, limit: int) -> str:
        if not items:
            return "无"
        return "、".join(f"{x.get('name', '-')}{x.get('code', '-')[-3:]}" for x in items[:limit])

    lines = [
        f"A股中小盘 09:35 筛选",
        f"时间：{generated_at}",
        f"结论：{summary}",
        f"真龙头：{short(true_leaders, 3)}",
        f"强跟随：{short(strong_followers, 4)}",
        f"盯盘：{short(watchlist, 5)}",
        "邮件已同步发送到两个邮箱。",
    ]
    return "\n".join(lines)


def send_qq_brief(message: str) -> None:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        OPENCLAW_CMD,
        "message",
        "send",
        "--channel",
        QQBOT_CHANNEL,
        "--target",
        QQBOT_TARGET,
        "--message",
        message,
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_line(f"send_qq_brief rc={completed.returncode}")
    if completed.stdout.strip():
        log_line(f"send_qq_brief_stdout={completed.stdout.strip()[:1000]}")
    if completed.stderr.strip():
        log_line(f"send_qq_brief_stderr={completed.stderr.strip()[:1000]}")
    if completed.returncode != 0:
        raise RuntimeError(
            "QQ简报发送失败\n"
            f"rc={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )


def send_email(subject: str, body: str, retries: int = 3, retry_delay: int = 8) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            msg = EmailMessage()
            msg["From"] = SENDER
            msg["To"] = ", ".join(RECEIVERS)
            msg["Subject"] = subject
            msg.set_content(body, subtype="plain", charset="utf-8")

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
                server.login(SENDER, AUTH_CODE)
                server.send_message(msg)
            log_line(f"send_email success attempt={attempt}")
            return
        except Exception as e:
            last_error = e
            log_line(f"send_email failed attempt={attempt} error={e}")
            if attempt < retries:
                time.sleep(retry_delay)
    raise RuntimeError(f"邮件发送失败，重试{retries}次后仍未成功：{last_error}")


def main() -> int:
    skipped, reason = guard_non_trading_day('smallcap_opening_mailer')
    if skipped:
        log_line(f"skip_non_trading_day reason={reason}")
        return 0

    payload = run_plugin()
    body = build_text_report(payload)
    qq_brief = build_qq_brief(payload)
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d")
    weekday = WEEKDAY_CN[now.weekday()]
    subject = f"【沈万三】A股中小盘强势早盘筛选 - {stamp} {weekday}"

    txt_path = REPORT_DIR / "latest_smallcap_mail.txt"
    txt_path.write_text(body, encoding="utf-8")
    brief_path = REPORT_DIR / "latest_smallcap_qq_brief.txt"
    brief_path.write_text(qq_brief, encoding="utf-8")
    log_line(f"report_saved={txt_path}")
    log_line(f"qq_brief_saved={brief_path}")

    send_qq_brief(qq_brief)
    send_email(subject, body)
    print("SMALLCAP_MAIL_OK")
    print(txt_path)
    print(brief_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

