import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from datasource.tencent import fetch

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUTPUT_DIR / "tencent_feasibility_probe.json"


def main():
    sample = [
        "sz000001", "sz000002", "sz000333", "sz000651", "sz000858",
        "sz002001", "sz002230", "sz002371", "sz002475", "sz002594",
    ]
    rows = []
    started = time.time()
    success = 0
    for symbol in sample:
        t0 = time.time()
        result = fetch(symbol, "auto_today")
        elapsed = round(time.time() - t0, 2)
        ok = bool(result.get("ok"))
        if ok:
            success += 1
        ticks = ((result.get("raw") or {}).get("auction_ticks") or [])
        rows.append({
            "symbol": symbol,
            "ok": ok,
            "elapsed_seconds": elapsed,
            "error": result.get("error"),
            "tick_count": len(ticks),
            "first_tick": ticks[0]["time"] if ticks else None,
            "last_tick": ticks[-1]["time"] if ticks else None,
        })
    total = round(time.time() - started, 2)
    report = {
        "sample_size": len(sample),
        "success_count": success,
        "failure_count": len(sample) - success,
        "success_rate": round(success / len(sample), 4) if sample else 0,
        "total_seconds": total,
        "avg_seconds_per_symbol": round(total / len(sample), 2) if sample else 0,
        "rows": rows,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
