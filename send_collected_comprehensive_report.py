from __future__ import annotations

from pathlib import Path
from daily_comprehensive_report import send_email, build_report

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
subject_path = OUT_DIR / "latest_subject.txt"
text_path = OUT_DIR / "latest_report.txt"
html_path = OUT_DIR / "latest_report.html"

if subject_path.exists() and text_path.exists() and html_path.exists():
    subject = subject_path.read_text(encoding="utf-8")
    text_body = text_path.read_text(encoding="utf-8")
    html_body = html_path.read_text(encoding="utf-8")
else:
    subject, text_body, html_body = build_report()

send_email(subject, text_body, html_body)
print("SEND_OK")
print(subject)
