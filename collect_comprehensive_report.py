from __future__ import annotations

import json
from pathlib import Path
from daily_comprehensive_report import build_report

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
OUT_DIR.mkdir(parents=True, exist_ok=True)

subject, text_body, html_body = build_report()

(OUT_DIR / "latest_subject.txt").write_text(subject, encoding="utf-8")
(OUT_DIR / "latest_report.txt").write_text(text_body, encoding="utf-8")
(OUT_DIR / "latest_report.html").write_text(html_body, encoding="utf-8")
(OUT_DIR / "latest_report.json").write_text(
    json.dumps({"subject": subject, "text": text_body, "html": html_body}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("COLLECT_OK")
print(subject)
print(str(OUT_DIR / "latest_report.txt"))
