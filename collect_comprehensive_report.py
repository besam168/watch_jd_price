from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from daily_comprehensive_report import build_report

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RUN_LOG = LOG_DIR / "collect_comprehensive_report.log"
STATUS_JSON = OUT_DIR / "latest_collect_status.json"
CONFIG_PATH = ROOT / "skills" / "scheduled-report-mailer" / "config" / "report-config.json"
RUN_ID = os.environ.get("SWS_COLLECT_RUN_ID") or dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
RUN_LOG_BY_ID = LOG_DIR / f"collect_comprehensive_report-{RUN_ID}.log"


def append_log(text: str) -> None:
    line = f"[{RUN_ID}] {text.rstrip()}\n"
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(line)
    with RUN_LOG_BY_ID.open("a", encoding="utf-8") as f:
        f.write(line)


def timed_step(label: str, fn, *args, **kwargs):
    started = time.perf_counter()
    append_log(f"===== {label} START =====")
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - started
    append_log(f"===== {label} END elapsed={elapsed:.2f}s =====")
    return result, elapsed


def load_whitelist_urls() -> list[str]:
    if not CONFIG_PATH.exists():
        return []
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    urls = cfg.get("collection_policy", {}).get("whitelist_urls", [])
    if not isinstance(urls, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for u in urls:
        url = str(u or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        cleaned.append(url)
    return cleaned


def probe_url(url: str, timeout_seconds: int = 18) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClaw/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Range": "bytes=0-4096",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    started = dt.datetime.now().isoformat()
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            body = resp.read(4096)
            content_type = resp.headers.get("Content-Type", "")
            ok = 200 <= int(status) < 400
            return {
                "url": url,
                "ok": bool(ok),
                "status": int(status),
                "bytes": len(body or b""),
                "contentType": content_type,
                "startedAt": started,
                "finishedAt": dt.datetime.now().isoformat(),
                "error": "",
            }
    except urllib.error.HTTPError as e:
        return {
            "url": url,
            "ok": False,
            "status": int(e.code),
            "bytes": 0,
            "contentType": "",
            "startedAt": started,
            "finishedAt": dt.datetime.now().isoformat(),
            "error": f"HTTPError: {e}",
        }
    except Exception as e:
        return {
            "url": url,
            "ok": False,
            "status": None,
            "bytes": 0,
            "contentType": "",
            "startedAt": started,
            "finishedAt": dt.datetime.now().isoformat(),
            "error": str(e),
        }


def run_whitelist_full_probe(urls: list[str]) -> dict:
    results: list[dict] = []
    append_log(f"===== FULL_WHITELIST_PROBE_START count={len(urls)} =====")
    for idx, url in enumerate(urls, start=1):
        row = probe_url(url)
        results.append(row)
        marker = "OK" if row["ok"] else "FAIL"
        append_log(
            f"[{idx:02d}/{len(urls):02d}] {marker} status={row.get('status')} bytes={row.get('bytes')} url={url}"
        )
        if row.get("error"):
            append_log(f"  error: {row['error']}")
    ok_count = sum(1 for x in results if x.get("ok"))
    fail_count = len(results) - ok_count
    append_log(f"===== FULL_WHITELIST_PROBE_END ok={ok_count} fail={fail_count} =====")
    return {
        "plannedUrlCount": len(urls),
        "touchedUrlCount": len(results),
        "okCount": ok_count,
        "failCount": fail_count,
        "results": results,
    }


append_log("===== COLLECT START =====")
append_log("Mode switched: force full whitelist crawl every run.")

refresh_script = ROOT / "refresh_qveris_market_snapshot.py"
refresh_rc = None
refresh_elapsed = None
refresh_stdout = ""
refresh_stderr = ""
refresh_snapshot_valid = False
refresh_snapshot_reason = "not-run"
core_snapshot_keys = {"SPX", "IXIC", "DJI"}
if refresh_script.exists():
    try:
        def _run_refresh():
            return subprocess.run(
                ["python", str(refresh_script)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )

        completed, refresh_elapsed = timed_step("REFRESH_MARKET_SNAPSHOT", _run_refresh)
        refresh_rc = completed.returncode
        refresh_stdout = completed.stdout or ""
        refresh_stderr = completed.stderr or ""
        append_log(f"===== REFRESH_MARKET_SNAPSHOT rc={completed.returncode} =====")
        append_log(refresh_stdout or "(no refresh stdout)")
        if refresh_stderr:
            append_log("[refresh stderr]")
            append_log(refresh_stderr)
    except Exception as e:
        refresh_rc = -1
        refresh_stderr = str(e)
        append_log(f"REFRESH_MARKET_SNAPSHOT_EXCEPTION: {e}")

snapshot_path = OUT_DIR / "qveris_market_snapshot.json"
if refresh_rc in (0, None) and snapshot_path.exists():
    try:
        snapshot_obj = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if isinstance(snapshot_obj, dict) and any(k in snapshot_obj for k in core_snapshot_keys):
            refresh_snapshot_valid = True
            refresh_snapshot_reason = "core-keys-present"
        else:
            refresh_snapshot_reason = "missing-core-keys"
    except Exception as e:
        refresh_snapshot_reason = f"invalid-json: {e}"
elif refresh_rc in (0, None):
    refresh_snapshot_reason = "snapshot-file-missing"
else:
    refresh_snapshot_reason = f"refresh-rc={refresh_rc}"

append_log(
    f"===== REFRESH_MARKET_SNAPSHOT VALIDATION ok={refresh_snapshot_valid} reason={refresh_snapshot_reason} path={snapshot_path} ====="
)

whitelist_urls = load_whitelist_urls()
probe_summary, probe_elapsed = timed_step("FULL_WHITELIST_PROBE", run_whitelist_full_probe, whitelist_urls)

(subject, text_body, html_body), build_report_elapsed = timed_step("BUILD_REPORT", build_report)

headline_count = len([line for line in text_body.splitlines() if re.match(r"^\d+\. ", line)])
headline_evidence_count = text_body.count("已抓正文")
evidence_summary = {
    "headlineCount": headline_count,
    "headlineEvidenceCount": headline_evidence_count,
    "hasPlaceholderSearchDiscovery": "搜索发现（待正文交叉验证）" in text_body,
}
append_log("===== HEADLINE_EVIDENCE =====")
append_log(json.dumps(evidence_summary, ensure_ascii=False, indent=2))

collect_status = {
    "generatedAt": dt.datetime.now().isoformat(),
    "runId": RUN_ID,
    "runLogPath": str(RUN_LOG_BY_ID),
    "mode": "full-whitelist-crawl-every-run",
    "timings": {
        "refreshMarketSnapshotSeconds": refresh_elapsed,
        "fullWhitelistProbeSeconds": probe_elapsed,
        "buildReportSeconds": build_report_elapsed,
    },
    "freshnessWindowHours": {"min": 24, "max": 48},
    "plannedWhitelistUrlCount": len(whitelist_urls),
    "touchedWhitelistUrlCount": probe_summary["touchedUrlCount"],
    "ok_groups": [
        *( ["full_whitelist_probe"] if probe_summary["okCount"] > 0 else []),
        *( ["market_snapshot_refresh"] if refresh_snapshot_valid else []),
        *( ["headline_evidence_gate"] if headline_evidence_count >= 1 and not evidence_summary["hasPlaceholderSearchDiscovery"] else []),
    ],
    "failed_groups": [
        *( [] if probe_summary["failCount"] == 0 else ["full_whitelist_probe_partial_fail"]),
        *( [] if refresh_snapshot_valid else ["market_snapshot_refresh"]),
        *( [] if headline_evidence_count >= 1 and not evidence_summary["hasPlaceholderSearchDiscovery"] else ["headline_evidence_gate"]),
    ],
    "results": [
        {
            "group": "full_whitelist_probe",
            "returncode": 0 if probe_summary["okCount"] > 0 else 2,
            "ok": probe_summary["okCount"] > 0,
            "stdout": f"full whitelist probe touched {probe_summary['touchedUrlCount']} urls, ok={probe_summary['okCount']}, fail={probe_summary['failCount']}",
            "stderr": "",
            "urlCount": probe_summary["touchedUrlCount"],
            "okCount": probe_summary["okCount"],
            "failCount": probe_summary["failCount"],
            "items": probe_summary["results"],
        },
        {
            "group": "market_snapshot_refresh",
            "returncode": 0 if refresh_snapshot_valid else (refresh_rc if refresh_rc is not None else 2),
            "ok": refresh_snapshot_valid,
            "stdout": refresh_stdout or ("refresh_market_snapshot executed" if refresh_rc is not None else "refresh script not found, skipped"),
            "stderr": refresh_stderr,
            "validation": {
                "ok": refresh_snapshot_valid,
                "reason": refresh_snapshot_reason,
                "path": str(snapshot_path),
            },
            "urlCount": 0,
        },
        {
            "group": "headline_evidence_gate",
            "returncode": 0 if headline_evidence_count >= 1 and not evidence_summary["hasPlaceholderSearchDiscovery"] else 2,
            "ok": bool(headline_evidence_count >= 1 and not evidence_summary["hasPlaceholderSearchDiscovery"]),
            "stdout": json.dumps(evidence_summary, ensure_ascii=False),
            "stderr": "",
            "urlCount": headline_count,
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
(OUT_DIR / "latest_report_evidence.json").write_text(json.dumps(evidence_summary, ensure_ascii=False, indent=2), encoding="utf-8")
STATUS_JSON.write_text(json.dumps(collect_status, ensure_ascii=False, indent=2), encoding="utf-8")

append_log("===== COLLECT END rc=0 =====")
print("COLLECT_OK")
print(f"RUN_ID: {RUN_ID}")
print(f"RUN_LOG: {RUN_LOG_BY_ID}")
print(subject)
print(str(OUT_DIR / "latest_report.txt"))
failed_group_names = collect_status.get("failed_groups", [])
if failed_group_names:
    print("FAILED_GROUPS:", ", ".join(failed_group_names))
else:
    print("FAILED_GROUPS: none")
