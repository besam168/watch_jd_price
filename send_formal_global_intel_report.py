from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from formal_global_intel_report import send_email

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
STATE_PATH = OUT_DIR / "formal_pipeline_state.json"
SUBJECT_PATH = OUT_DIR / "latest_subject.txt"
TEXT_PATH = OUT_DIR / "latest_report.txt"
HTML_PATH = OUT_DIR / "latest_report.html"

TZ_CN = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(TZ_CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def send_latest() -> str:
    state = load_state()
    if not state.get("lastCollectOk"):
        raise RuntimeError("latest collect is not marked successful")
    if not (SUBJECT_PATH.exists() and TEXT_PATH.exists() and HTML_PATH.exists()):
        raise FileNotFoundError("latest report artifacts are incomplete")

    subject = SUBJECT_PATH.read_text(encoding="utf-8")
    text_body = TEXT_PATH.read_text(encoding="utf-8")
    html_body = HTML_PATH.read_text(encoding="utf-8")

    send_email(subject, text_body, html_body)
    state["lastSendAt"] = now_iso()
    state["lastSendOk"] = True
    state["lastSentSubject"] = subject
    save_state(state)
    return subject


if __name__ == "__main__":
    subject = send_latest()
    print("SEND_OK")
    print(subject)
