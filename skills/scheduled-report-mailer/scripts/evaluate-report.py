from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = SKILL_ROOT / "config" / "report-config.json"
OUT_STATUS = SKILL_ROOT / "state" / "report-evaluation.json"

KEYWORD_MAP = {
    "gaza": ["加沙", "gaza", "哈马斯"],
    "ukraine": ["乌克兰", "ukraine", "俄乌", "russia-ukraine"],
    "us-china-trade": ["中美经贸", "中美关系", "trade", "tariff", "china", "美国关税"],
    "us-equities": ["S&P 500", "纳斯达克", "道琼斯", "美股"],
    "gold": ["黄金", "gold", "XAU"],
    "brent": ["布伦特", "brent"]
}


def main() -> int:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    must_check = cfg.get("collection_policy", {}).get("must_check", [])
    report_path = ROOT / cfg.get("paths", {}).get("latest_report_txt", "reports/scheduled/latest_report.txt")
    text = report_path.read_text(encoding="utf-8", errors="replace") if report_path.exists() else ""

    checks = {}
    for item in must_check:
        keywords = KEYWORD_MAP.get(item, [item])
        matched = [kw for kw in keywords if kw.lower() in text.lower()]
        checks[item] = {
            "ok": bool(matched),
            "matchedKeywords": matched,
        }

    result = {
        "generatedAt": datetime.now().isoformat(),
        "reportPath": str(report_path),
        "mustCheckResults": checks,
        "summary": {
            "okCount": sum(1 for v in checks.values() if v["ok"]),
            "total": len(checks),
        },
    }
    OUT_STATUS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_STATUS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
