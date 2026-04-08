from __future__ import annotations

import json
from pathlib import Path

try:
    from qveris_report_helpers import fetch_stock_quote, fetch_commodity_quote
except Exception:
    fetch_stock_quote = None
    fetch_commodity_quote = None

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "scheduled" / "qveris_market_snapshot.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

result: dict[str, object] = {}

proxy_indices = {
    "SPY": "SPX",
    "QQQ": "IXIC",
    "DIA": "DJI",
    "EWU": "FTSE",
    "EWJ": "N225",
    "EWH": "HSI",
    "EWT": "TWII",
    "EWY": "KOSPI",
}

if fetch_stock_quote is not None:
    for symbol in ["AAPL", "NVDA", "TSLA"]:
        try:
            data = fetch_stock_quote(symbol)
        except Exception:
            data = None
        if isinstance(data, dict) and (data.get("c") or data.get("price")):
            result[symbol] = data

    for proxy_symbol, alias in proxy_indices.items():
        try:
            data = fetch_stock_quote(proxy_symbol)
        except Exception:
            data = None
        if isinstance(data, dict) and (data.get("c") or data.get("price")):
            result[alias] = data
            result[f"{alias}_proxy"] = proxy_symbol

if fetch_commodity_quote is not None:
    commodity_symbols = [("XAUUSD", "XAUUSD"), ("BZUSD", "BZUSD"), ("CLUSD", "CLUSD")]
    for symbol, alias in commodity_symbols:
        try:
            data = fetch_commodity_quote(symbol)
        except Exception:
            data = None
        if isinstance(data, dict):
            if isinstance(data, list) and data:
                data = data[0]
            if isinstance(data, dict) and (data.get("price") or data.get("c")):
                result[alias] = data

OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(OUT))
