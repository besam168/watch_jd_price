from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

from formal_global_intel_report import collect_news, build_text_report, build_html_report, NOW

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
LOG_DIR = ROOT / "logs"
STATE_PATH = OUT_DIR / "formal_pipeline_state.json"
STATUS_PATH = OUT_DIR / "latest_collect_status.json"
SUBJECT_PATH = OUT_DIR / "latest_subject.txt"
TEXT_PATH = OUT_DIR / "latest_report.txt"
HTML_PATH = OUT_DIR / "latest_report.html"
PREVIEW_TXT_PATH = OUT_DIR / "formal_preview.txt"
PREVIEW_HTML_PATH = OUT_DIR / "formal_preview.html"

TZ_CN = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(TZ_CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def append_log(message: str) -> None:
    ensure_dirs()
    line = f"[{datetime.now(TZ_CN).strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
    (LOG_DIR / "formal_global_intel_report.log").open("a", encoding="utf-8").write(line)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_and_render() -> dict:
    ensure_dirs()
    subject = f"全球综合情报报告 - {NOW.strftime('%Y-%m-%d %H:%M')}"
    try:
        append_log("collect:start")
        grouped, focus_hits, errors = collect_news()
        text_body = build_text_report(grouped, focus_hits, errors)
        html_body = build_html_report(grouped, focus_hits, errors)

        SUBJECT_PATH.write_text(subject, encoding="utf-8")
        TEXT_PATH.write_text(text_body, encoding="utf-8")
        HTML_PATH.write_text(html_body, encoding="utf-8")
        PREVIEW_TXT_PATH.write_text(text_body, encoding="utf-8")
        PREVIEW_HTML_PATH.write_text(html_body, encoding="utf-8")

        state = {
            "lastCollectAt": now_iso(),
            "lastCollectOk": True,
            "lastSubject": subject,
            "textPath": str(TEXT_PATH),
            "htmlPath": str(HTML_PATH),
            "previewTextPath": str(PREVIEW_TXT_PATH),
            "previewHtmlPath": str(PREVIEW_HTML_PATH),
            "errors": errors,
        }
        status = {
            "ok": True,
            "collectedAt": now_iso(),
            "subject": subject,
            "errorCount": len(errors),
            "errors": errors,
        }
        write_json(STATE_PATH, state)
        write_json(STATUS_PATH, status)
        append_log(f"collect:ok subject={subject}")
        return {"ok": True, "subject": subject, "errors": errors}
    except Exception as e:
        tb = traceback.format_exc()
        state = {
            "lastCollectAt": now_iso(),
            "lastCollectOk": False,
            "lastError": str(e),
            "traceback": tb,
        }
        status = {
            "ok": False,
            "collectedAt": now_iso(),
            "error": str(e),
        }
        write_json(STATE_PATH, state)
        write_json(STATUS_PATH, status)
        append_log(f"collect:fail error={e}")
        raise


if __name__ == "__main__":
    result = collect_and_render()
    print("COLLECT_OK")
    print(result["subject"])
    print(str(PREVIEW_TXT_PATH))
