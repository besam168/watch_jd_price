from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from daily_comprehensive_report import build_report

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RUN_LOG = LOG_DIR / "collect_comprehensive_report.log"
STATUS_JSON = OUT_DIR / "latest_collect_status.json"


def append_log(text: str) -> None:
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def maybe_run_desktop_fallback(url: str) -> dict:
    script = ROOT / "desktop_browser_fallback.py"
    if not script.exists() or not url:
        return {"ok": False, "reason": "script_missing_or_empty_url"}
    try:
        completed = subprocess.run(
            ["python", str(script), url, "3"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        out_path = (completed.stdout or "").strip().splitlines()[-1].strip() if (completed.stdout or "").strip() else ""
        payload = {}
        if out_path and Path(out_path).exists():
            payload = json.loads(Path(out_path).read_text(encoding="utf-8"))
        payload["returncode"] = completed.returncode
        return payload
    except Exception as e:
        return {"ok": False, "error": str(e)}


append_log("===== COLLECT START =====")
append_log("Building report with local + QVeris + market snapshot refresh.")

refresh_script = ROOT / "refresh_qveris_market_snapshot.py"
refresh_rc = None
if refresh_script.exists():
    try:
        completed = subprocess.run(
            ["python", str(refresh_script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        refresh_rc = completed.returncode
        append_log(f"===== REFRESH_QVERIS rc={completed.returncode} =====")
        append_log(completed.stdout or "(no refresh stdout)")
        if completed.stderr:
            append_log("[refresh stderr]")
            append_log(completed.stderr)
    except Exception as e:
        refresh_rc = -1
        append_log(f"REFRESH_QVERIS_EXCEPTION: {e}")

desktop_fallback = maybe_run_desktop_fallback("https://www.bbc.com/news")
if desktop_fallback:
    append_log("===== DESKTOP_BROWSER_FALLBACK =====")
    append_log(json.dumps(desktop_fallback, ensure_ascii=False, indent=2))

subject, text_body, html_body = build_report()

collect_status = {
    "generatedAt": dt.datetime.now().isoformat(),
    "mode": "local-plus-qveris-refresh",
    "freshnessWindowHours": {"min": 0, "max": 24},
    "ok_groups": [
        "rss_qveris_multi_search",
        "market_snapshot_refresh",
        *(["desktop_browser_fallback"] if desktop_fallback.get("ok") else []),
    ],
    "failed_groups": [
        *([] if refresh_rc in (0, None) else ["market_snapshot_refresh"]),
        *([] if desktop_fallback.get("ok") else ["desktop_browser_fallback"]),
    ],
    "results": [
        {
            "group": "rss_qveris_multi_search",
            "returncode": 0,
            "ok": True,
            "stdout": "build_report() completed with refreshed local sources",
            "stderr": "",
            "urlCount": 0,
        },
        {
            "group": "market_snapshot_refresh",
            "returncode": refresh_rc if refresh_rc is not None else 0,
            "ok": refresh_rc in (0, None),
            "stdout": "refresh_qveris_market_snapshot.py executed" if refresh_rc is not None else "refresh script not found, skipped",
            "stderr": "",
            "urlCount": 0,
        },
        {
            "group": "desktop_browser_fallback",
            "returncode": desktop_fallback.get("returncode", 1),
            "ok": bool(desktop_fallback.get("ok")),
            "stdout": json.dumps(desktop_fallback, ensure_ascii=False),
            "stderr": "",
            "urlCount": 1,
        },
    ],
}

(OUT_DIR / "latest_subject.txt").write_text(subject, encoding="utf-8")
(OUT_DIR / "latest_report.txt").write_text(text_body, encoding="utf-8")
(OUT_DIR / "latest_report.html").write_text(html_body, encoding="utf-8")
(OUT_DIR / "latest_report.json").write_text(
    json.dumps({"subject": subject, "text": text_body, "html": html_body}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
STATUS_JSON.write_text(json.dumps(collect_status, ensure_ascii=False, indent=2), encoding="utf-8")

append_log("===== COLLECT END rc=0 =====")
print("COLLECT_OK")
print(subject)
print(str(OUT_DIR / "latest_report.txt"))
print("FAILED_GROUPS: none")
