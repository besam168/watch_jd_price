from pathlib import Path

from core.filters import apply_filters
from core.metrics import calc_metrics
from core.scoring import calc_smooth_score
from datasource import tencent, eastmoney, sina
from datasource.helpers import normalize_symbol, is_sz_mainboard_target
from datasource.normalize import normalize_payload
from output.writer import write_outputs
from config import ScanConfig

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
UNIVERSE_PATH = OUTPUT_DIR / "sz_mainboard_00_universe.json"


def load_universe(cfg: ScanConfig) -> list[str]:
    if cfg.universe_mode == "custom" and cfg.custom_symbols:
        return [normalize_symbol(x) for x in cfg.custom_symbols if is_sz_mainboard_target(x)]

    if UNIVERSE_PATH.exists():
        import json
        obj = json.loads(UNIVERSE_PATH.read_text(encoding="utf-8"))
        selected = obj.get("selected") or []
        return [normalize_symbol(x.get("code", "")) for x in selected if x.get("code")]

    return []


def fetch_with_failover(symbol: str, date_text: str, enabled: bool = True):
    # 当前已确认 akshare/东方财富 pre-minute 路径可返回 09:15~09:25 的分钟序列，先放主位。
    chain = [eastmoney.fetch, tencent.fetch, sina.fetch]
    last = None
    for fn in chain:
        payload = fn(symbol, date_text)
        last = payload
        if payload.get("ok"):
            return payload
        if not enabled:
            break
    return last or {"ok": False, "source": "none", "error": "all_sources_failed"}


def build_row(symbol: str, name: str, date_text: str, source: str, data_granularity: str, metrics, score: float, passed: bool, reasons: list[str]) -> dict:
    return {
        "symbol": symbol,
        "name": name,
        "date": date_text,
        "source": source,
        "data_granularity": data_granularity,
        "tick_count": metrics.tick_count,
        "auction_open_price": metrics.auction_open_price,
        "auction_last_price": metrics.auction_last_price,
        "auction_high": metrics.auction_high,
        "auction_low": metrics.auction_low,
        "range_ratio": metrics.range_ratio,
        "jump_std_ratio": metrics.jump_std_ratio,
        "change_ratio": metrics.change_ratio,
        "rmse_ratio": metrics.rmse_ratio,
        "auction_amt": metrics.auction_amt,
        "amt_float_ratio": metrics.amt_float_ratio,
        "smooth_score": score,
        "passed": passed,
        "fail_reasons": ";".join(reasons),
    }


def run(cfg: ScanConfig):
    symbols = load_universe(cfg)
    all_rows = []

    for symbol in symbols:
        payload = fetch_with_failover(symbol, cfg.date, cfg.runtime.failover_enabled)
        norm = normalize_payload(payload, symbol, cfg.date)
        if not norm:
            all_rows.append({
                "symbol": symbol,
                "name": symbol,
                "date": cfg.date,
                "source": payload.get("source", ""),
                "data_granularity": payload.get("data_granularity", "unknown"),
                "tick_count": 0,
                "auction_open_price": None,
                "auction_last_price": None,
                "auction_high": None,
                "auction_low": None,
                "range_ratio": None,
                "jump_std_ratio": None,
                "change_ratio": None,
                "rmse_ratio": None,
                "auction_amt": None,
                "amt_float_ratio": None,
                "smooth_score": 0.0,
                "passed": False,
                "fail_reasons": payload.get("error", "normalize_failed"),
            })
            continue

        metrics = calc_metrics(norm)
        passed, reasons = apply_filters(metrics, cfg.thresholds)
        score = calc_smooth_score(metrics, cfg.thresholds, cfg.scoring_weights)
        all_rows.append(build_row(norm.symbol, norm.name, norm.date, norm.source, norm.data_granularity, metrics, score, passed, reasons))

    passed_rows = [x for x in all_rows if x.get("passed")]
    passed_rows.sort(key=lambda x: x.get("smooth_score", 0), reverse=True)
    passed_rows = passed_rows[: cfg.top_n]
    outputs = write_outputs(BASE_DIR, str(cfg.date).replace("-", ""), passed_rows, all_rows)
    return passed_rows, all_rows, outputs
