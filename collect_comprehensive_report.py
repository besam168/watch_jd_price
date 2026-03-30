from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from daily_comprehensive_report import build_report

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCRAPE_GROUPS = [
    [
        "https://www.bbc.com/news",
        "https://www.reuters.com/",
        "https://apnews.com/",
        "https://www.aljazeera.com/",
        "https://www.cnbc.com/world/?region=world",
        "https://finance.yahoo.com/",
    ],
    [
        "https://www.nyse.com/index",
        "https://www.twse.com.tw/zh/index.html",
        "https://www.sse.com.cn/",
        "https://www.jpx.co.jp/english/",
        "https://global.krx.co.kr/main/main.jsp",
        "https://jp.investing.com/",
        "https://finance.naver.com/",
        "https://www.eastmoney.com/",
    ],
    [
        "https://www.reuters.com/world/europe/",
        "https://www.reuters.com/world/china/",
        "https://apnews.com/hub/russia-ukraine",
        "https://apnews.com/hub/china",
        "https://finance.yahoo.com/quote/GC=F/",
        "https://finance.yahoo.com/quote/BZ=F/",
        "https://finance.yahoo.com/quote/CL=F/",
    ],
]

FIRECRAWL_BIN = shutil.which("firecrawl") or "C:\\Users\\besam\\AppData\\Roaming\\npm\\firecrawl.cmd"


def run_scrape(urls: list[str]) -> None:
    cmd = [FIRECRAWL_BIN, "scrape", *urls, "--only-main-content", "--wait-for", "3000"]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, shell=False)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr)
        raise SystemExit(proc.returncode)


for group in SCRAPE_GROUPS:
    run_scrape(group)

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
