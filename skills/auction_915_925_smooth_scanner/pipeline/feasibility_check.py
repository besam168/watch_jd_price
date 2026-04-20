import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUTPUT_DIR / "full_scan_feasibility.json"


def estimate(total_symbols: int, avg_seconds_per_symbol: float, concurrency: int, fail_rate: float) -> dict:
    effective = max(1, concurrency)
    total_seconds = (total_symbols * avg_seconds_per_symbol) / effective
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_symbols": total_symbols,
        "avg_seconds_per_symbol": avg_seconds_per_symbol,
        "concurrency": concurrency,
        "estimated_total_seconds": round(total_seconds, 2),
        "estimated_total_minutes": round(total_seconds / 60.0, 2),
        "assumed_fail_rate": fail_rate,
    }


if __name__ == "__main__":
    report = estimate(total_symbols=1600, avg_seconds_per_symbol=1.1, concurrency=20, fail_rate=0.15)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
