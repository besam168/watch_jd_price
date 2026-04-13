from __future__ import annotations

from pathlib import Path
from formal_global_intel_report import collect_news, build_text_report, build_html_report, send_email, NOW

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
    grouped, focus_hits, errors = collect_news()
    subject = f"全球综合情报报告 - {NOW.strftime('%Y-%m-%d %H:%M')}"
    text_body = build_text_report(grouped, focus_hits, errors)
    html_body = build_html_report(grouped, focus_hits, errors)

send_email(subject, text_body, html_body)
print("SEND_OK")
print(subject)
