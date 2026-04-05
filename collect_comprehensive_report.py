from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path
from daily_comprehensive_report import build_report

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "scheduled"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SCRAPE_GROUPS = [
    {
        "name": "news_core",
        "urls": [
            "https://www.bbc.com/news",
            "https://www.theguardian.com/international",
            "https://www.reuters.com/",
            "https://apnews.com/",
            "https://www.npr.org/",
            "https://www.aljazeera.com/",
            "https://www.dw.com/zh/%E5%9C%A8%E7%BA%BF%E6%8A%A5%E5%AF%BC/s-9058",
            "https://www.france24.com/en/",
            "https://www.cnbc.com/world/?region=world",
            "https://www.usatoday.com/",
            "https://finance.yahoo.com/",
        ],
    },
    {
        "name": "markets_global",
        "urls": [
            "https://www.nyse.com/index",
            "https://www.jpx.co.jp/english/",
            "https://global.krx.co.kr/main/main.jsp",
            "https://finance.naver.com/",
            "https://www.twse.com.tw/zh/index.html",
            "https://tw.stock.yahoo.com/",
            "https://www.sse.com.cn/",
            "https://jp.investing.com/",
            "https://www.eastmoney.com/",
        ],
    },
    {
        "name": "deep_dive",
        "urls": [
            "https://www.reuters.com/world/europe/",
            "https://www.reuters.com/world/china/",
            "https://apnews.com/hub/russia-ukraine",
            "https://apnews.com/hub/china",
            "https://finance.yahoo.com/quote/GC=F/",
            "https://finance.yahoo.com/quote/BZ=F/",
            "https://finance.yahoo.com/quote/CL=F/",
        ],
    },
    {
        "name": "tech_ai_robotics",
        "urls": [
            "https://www.theverge.com/",
            "https://techcrunch.com/",
            "https://spectrum.ieee.org/",
            "https://www.wired.com/",
            "https://arstechnica.com/",
            "https://www.technologyreview.com/",
            "https://venturebeat.com/category/ai/",
            "https://singularityhub.com/",
            "https://www.artificialintelligence-news.com/",
            "https://www.engadget.com/",
        ],
    },
]

FIRECRAWL_BIN = shutil.which("firecrawl") or "C:\\Users\\besam\\AppData\\Roaming\\npm\\firecrawl.cmd"
RUN_LOG = LOG_DIR / "collect_comprehensive_report.log"
STATUS_JSON = OUT_DIR / "latest_collect_status.json"


def append_log(text: str) -> None:
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def run_scrape(name: str, urls: list[str]) -> dict[str, object]:
    cmd = [FIRECRAWL_BIN, "scrape", *urls, "--only-main-content", "--wait-for", "3000"]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, shell=False)
    result = {
        "group": name,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "urlCount": len(urls),
    }
    append_log(f"===== GROUP {name} START =====")
    append_log(proc.stdout or "(no stdout)")
    if proc.stderr:
        append_log("[stderr]")
        append_log(proc.stderr)
    append_log(f"===== GROUP {name} END rc={proc.returncode} =====")
    return result


results: list[dict[str, object]] = []
for group in SCRAPE_GROUPS:
    result = run_scrape(group["name"], group["urls"])
    results.append(result)
    status = "OK" if result["ok"] else "FAILED"
    print(f"SCRAPE_GROUP_{status}: {group['name']}")

subject, text_body, html_body = build_report()

ok_groups = [r["group"] for r in results if r["ok"]]
failed_groups = [r["group"] for r in results if not r["ok"]]
collect_status = {
    "generatedAt": dt.datetime.now().isoformat(),
    "freshnessWindowHours": {"min": 12, "max": 24},
    "firecrawl_bin": FIRECRAWL_BIN,
    "ok_groups": ok_groups,
    "failed_groups": failed_groups,
    "results": results,
}

(OUT_DIR / "latest_subject.txt").write_text(subject, encoding="utf-8")
(OUT_DIR / "latest_report.txt").write_text(text_body, encoding="utf-8")
(OUT_DIR / "latest_report.html").write_text(html_body, encoding="utf-8")
(OUT_DIR / "latest_report.json").write_text(
    json.dumps({"subject": subject, "text": text_body, "html": html_body}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
STATUS_JSON.write_text(json.dumps(collect_status, ensure_ascii=False, indent=2), encoding="utf-8")

print("COLLECT_OK")
print(subject)
print(str(OUT_DIR / "latest_report.txt"))
if failed_groups:
    print("FAILED_GROUPS:", ", ".join(failed_groups))
else:
    print("FAILED_GROUPS: none")
