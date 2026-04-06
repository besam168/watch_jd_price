from __future__ import annotations

import datetime as dt
import json
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


append_log("===== COLLECT START =====")
append_log("Firecrawl disabled by local fallback mode. Building report from RSS / QVeris / multi-search sources.")

subject, text_body, html_body = build_report()

collect_status = {
    "generatedAt": dt.datetime.now().isoformat(),
    "mode": "fallback-no-firecrawl",
    "freshnessWindowHours": {"min": 12, "max": 24},
    "ok_groups": ["rss_qveris_multi_search"],
    "failed_groups": [],
    "results": [
        {
            "group": "rss_qveris_multi_search",
            "returncode": 0,
            "ok": True,
            "stdout": "build_report() completed without Firecrawl",
            "stderr": "",
            "urlCount": 0,
        }
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
