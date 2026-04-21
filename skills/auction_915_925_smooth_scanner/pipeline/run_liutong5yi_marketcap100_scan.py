import argparse
import json
import math
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from datasource.pytdx_snapshot import fetch_quotes_with_fallback

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UNIVERSE_PATH = OUTPUT_DIR / "liutong5yi_marketcap100yi_universe_full.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Run liutong5yi + marketcap100yi auction smooth scan via pytdx snapshots.")
    parser.add_argument("--limit", type=int, default=500, help="Number of symbols to scan; use 0 or negative for full universe.")
    parser.add_argument("--full", action="store_true", help="Scan the full liutong5yi + marketcap100yi universe.")
    parser.add_argument("--rounds", type=int, default=3, help="Number of polling rounds.")
    parser.add_argument("--interval-seconds", type=int, default=3, help="Sleep seconds between rounds.")
    return parser.parse_args()


def load_universe(limit: int | None = None):
    obj = json.loads(UNIVERSE_PATH.read_text(encoding="utf-8"))
    selected = obj.get("selected") or []
    codes = [str(x.get("code")) for x in selected if x.get("code")]
    return codes[:limit] if limit and limit > 0 else codes


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def collect_round(symbols, chunk_size=120):
    rows = []
    stats = []
    for chunk in chunked(symbols, chunk_size):
        result = fetch_quotes_with_fallback(chunk, primary_batch_size=5)
        rows.extend(result["rows"])
        stats.append(result["stats"])
    return rows, stats


def reference_price(row: dict):
    bid1 = row.get("bid1")
    ask1 = row.get("ask1")
    try:
        bid = float(bid1)
    except Exception:
        bid = None
    try:
        ask = float(ask1)
    except Exception:
        ask = None
    if bid is not None and ask is not None and bid > 0 and ask > 0:
        return round((bid + ask) / 2, 4)
    if bid is not None and bid > 0:
        return round(bid, 4)
    if ask is not None and ask > 0:
        return round(ask, 4)
    return None


def summarize_track(points: list[dict]) -> dict:
    prices = [x["ref_price"] for x in points if x.get("ref_price") is not None]
    bid_vols = [float(x.get("bid_vol1") or 0) for x in points]
    ask_vols = [float(x.get("ask_vol1") or 0) for x in points]
    total_depth = [b + a for b, a in zip(bid_vols, ask_vols)]
    depth_changes = [abs(total_depth[i] - total_depth[i - 1]) for i in range(1, len(total_depth))] if len(total_depth) >= 2 else []
    if len(prices) < 2:
        return {"smooth_score": 0, "passed": False, "fail_reasons": "insufficient_points", "warnings": [], "tick_count": len(prices)}
    prev_close = points[0].get("last_close") or prices[0]
    diffs = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    changed = sum(1 for x in diffs if x != 0)
    positive_steps = sum(1 for x in diffs if x > 0)
    negative_steps = sum(1 for x in diffs if x < 0)
    x = list(range(len(prices)))
    x_mean = sum(x) / len(x)
    y_mean = sum(prices) / len(prices)
    den = sum((xi - x_mean) ** 2 for xi in x) or 1.0
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, prices)) / den
    intercept = y_mean - slope * x_mean
    fitted = [slope * xi + intercept for xi in x]
    rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(prices, fitted)) / len(prices))
    range_ratio = (max(prices) - min(prices)) / prev_close if prev_close else None
    jump_std_ratio = statistics.pstdev(diffs) / prev_close if prev_close and diffs else 0
    raw_change_ratio = changed / max(1, len(prices) - 1)
    up_drift_ratio = (prices[-1] - prices[0]) / prev_close if prev_close else 0
    monotonic_up = positive_steps >= 1 and negative_steps == 0
    gentle_up = monotonic_up and 0 < up_drift_ratio <= 0.012 and (jump_std_ratio or 0) <= 0.0012
    effective_change_ratio = min(raw_change_ratio, 0.33) if gentle_up else raw_change_ratio
    rmse_ratio = rmse / prev_close if prev_close else None
    depth_avg = statistics.mean(total_depth) if total_depth else 0
    depth_change_avg = statistics.mean(depth_changes) if depth_changes else 0
    score_range = max(0.0, 100.0 * (1.0 - (range_ratio / 0.004))) if range_ratio is not None else 0
    score_jump = max(0.0, 100.0 * (1.0 - (jump_std_ratio / 0.0015))) if jump_std_ratio is not None else 0
    score_change = max(0.0, 100.0 * (1.0 - (effective_change_ratio / 0.35))) if effective_change_ratio is not None else 0
    score_rmse = max(0.0, 100.0 * (1.0 - (rmse_ratio / 0.0018))) if rmse_ratio is not None else 0
    score_depth_change = max(0.0, 100.0 * (depth_change_avg / 20.0)) if depth_change_avg < 20 else 100.0
    score_up_drift = 100.0 if gentle_up else (70.0 if monotonic_up and up_drift_ratio > 0 else 0.0)
    flat_penalty = 18.0 if raw_change_ratio == 0 and up_drift_ratio == 0 else 0.0
    smooth_score = round(0.20 * score_range + 0.20 * score_jump + 0.14 * score_change + 0.14 * score_rmse + 0.10 * score_depth_change + 0.22 * score_up_drift - flat_penalty, 2)
    reasons = []
    warnings = []
    if range_ratio is not None and range_ratio > 0.004:
        reasons.append("range_ratio_exceeded")
    if jump_std_ratio is not None and jump_std_ratio > 0.0015:
        reasons.append("jump_std_ratio_exceeded")
    if effective_change_ratio > 0.35:
        reasons.append("change_ratio_exceeded")
    if rmse_ratio is not None and rmse_ratio > 0.0018:
        reasons.append("rmse_ratio_exceeded")
    if depth_avg < 800:
        reasons.append("depth_too_low")
    if depth_change_avg < 5:
        warnings.append("depth_change_too_low")
    if gentle_up:
        warnings.append("gentle_uptrend_allowed")
    return {
        "tick_count": len(prices),
        "auction_open_price": prices[0],
        "auction_last_price": prices[-1],
        "auction_high": max(prices),
        "auction_low": min(prices),
        "range_ratio": round(range_ratio, 6) if range_ratio is not None else None,
        "jump_std_ratio": round(jump_std_ratio, 6) if jump_std_ratio is not None else None,
        "change_ratio": round(raw_change_ratio, 6),
        "effective_change_ratio": round(effective_change_ratio, 6),
        "up_drift_ratio": round(up_drift_ratio, 6),
        "rmse_ratio": round(rmse_ratio, 6) if rmse_ratio is not None else None,
        "depth_avg": round(depth_avg, 2),
        "depth_change_avg": round(depth_change_avg, 2),
        "smooth_score": smooth_score,
        "passed": len(reasons) == 0,
        "fail_reasons": ";".join(reasons),
        "warnings": warnings,
    }


def main():
    args = parse_args()
    full_universe = load_universe(limit=None)
    symbols = full_universe if args.full else load_universe(limit=args.limit)
    rounds = args.rounds
    interval_seconds = args.interval_seconds
    tracks = {}
    round_reports = []
    scan_started = time.time()
    for i in range(rounds):
        started = time.time()
        rows, stats = collect_round(symbols, chunk_size=120)
        elapsed = round(time.time() - started, 4)
        round_reports.append({"round": i + 1, "elapsed_seconds": elapsed, "stats": stats})
        for row in rows:
            code = row.get("code")
            if not code:
                continue
            tracks.setdefault(code, []).append({
                "servertime": row.get("servertime"),
                "ref_price": reference_price(row),
                "last_close": row.get("last_close"),
                "bid1": row.get("bid1"),
                "ask1": row.get("ask1"),
                "bid_vol1": row.get("bid_vol1"),
                "ask_vol1": row.get("ask_vol1"),
            })
        if i < rounds - 1:
            time.sleep(interval_seconds)
    rows = []
    for code, points in tracks.items():
        summary = summarize_track(points)
        rows.append({"symbol": code, **summary})
    passed_rows = [x for x in rows if x.get("passed")]
    passed_rows.sort(key=lambda x: x.get("smooth_score", 0), reverse=True)
    failed_rows = [x for x in rows if not x.get("passed")]
    failed_rows.sort(key=lambda x: x.get("smooth_score", 0), reverse=True)
    elapsed_total = time.time() - scan_started
    estimated_full_universe_seconds = elapsed_total
    if len(symbols) > 0 and len(full_universe) > 0:
        estimated_full_universe_seconds = elapsed_total * len(full_universe) / len(symbols)
    out = {
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "universe_source": str(UNIVERSE_PATH),
        "full_universe_count": len(full_universe),
        "actual_scanned_count": len(symbols),
        "used_full_universe": bool(args.full or args.limit <= 0),
        "universe_count": len(symbols),
        "rounds": rounds,
        "interval_seconds": interval_seconds,
        "round_reports": round_reports,
        "elapsed_seconds_total": round(elapsed_total, 4),
        "estimated_full_universe_seconds": round(estimated_full_universe_seconds, 4),
        "passed_count": len(passed_rows),
        "failed_count": len(failed_rows),
        "passed_top20": passed_rows[:20],
        "filtered_highscore_top20": failed_rows[:20],
        "passed_all": passed_rows,
        "failed_all": failed_rows,
    }
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"auction_scan_liutong5yi_marketcap100yi_{ts}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(path), "actual_scanned_count": len(symbols), "full_universe_count": len(full_universe), "passed_count": len(passed_rows), "rounds": rounds, "interval_seconds": interval_seconds, "elapsed_seconds_total": round(elapsed_total, 4), "estimated_full_universe_seconds": round(estimated_full_universe_seconds, 4)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
