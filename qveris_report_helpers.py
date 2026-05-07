from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

YAHOO_SYMBOL_MAP = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "DIA": "DIA",
    "AAPL": "AAPL",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
    "XAUUSD": "GC=F",
    "BZUSD": "BZ=F",
    "CLUSD": "CL=F",
}


def _fetch_yahoo_quotes(symbols: list[str]) -> dict[str, dict]:
    yahoo_symbols = [YAHOO_SYMBOL_MAP[s] for s in symbols if s in YAHOO_SYMBOL_MAP]
    if not yahoo_symbols:
        return {}
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + ",".join(yahoo_symbols)
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}
    rows = payload.get("quoteResponse", {}).get("result", [])
    by_symbol: dict[str, dict] = {}
    reverse_map = {v: k for k, v in YAHOO_SYMBOL_MAP.items()}
    for row in rows:
        symbol = str(row.get("symbol") or "").strip()
        alias = reverse_map.get(symbol)
        if not alias:
            continue
        by_symbol[alias] = row
    return by_symbol


def _normalize_stock_quote(row: dict) -> dict:
    return {
        "price": row.get("regularMarketPrice"),
        "c": row.get("regularMarketPrice"),
        "pc": row.get("regularMarketPreviousClose"),
        "o": row.get("regularMarketOpen"),
        "h": row.get("regularMarketDayHigh"),
        "l": row.get("regularMarketDayLow"),
        "t": row.get("regularMarketTime"),
        "symbol": row.get("symbol"),
        "name": row.get("shortName") or row.get("longName"),
        "source": "yahoo_finance_public",
    }


def _normalize_commodity_quote(row: dict) -> dict:
    price = row.get("regularMarketPrice")
    previous = row.get("regularMarketPreviousClose")
    change = None
    change_pct = None
    try:
        if price is not None and previous not in (None, 0):
            change = float(price) - float(previous)
            change_pct = change / float(previous) * 100
    except Exception:
        pass
    return {
        "symbol": row.get("symbol"),
        "name": row.get("shortName") or row.get("longName"),
        "price": price,
        "open": row.get("regularMarketOpen"),
        "previousClose": previous,
        "dayLow": row.get("regularMarketDayLow"),
        "dayHigh": row.get("regularMarketDayHigh"),
        "change": change,
        "changePercentage": change_pct,
        "timestamp": row.get("regularMarketTime"),
        "source": "yahoo_finance_public",
    }


def fetch_news_items() -> list[dict[str, str]]:
    return []


def fetch_stock_quote(symbol: str) -> dict | None:
    row = _fetch_yahoo_quotes([symbol]).get(symbol)
    if not isinstance(row, dict):
        return None
    return _normalize_stock_quote(row)


def fetch_commodity_quote(symbol: str) -> dict | None:
    row = _fetch_yahoo_quotes([symbol]).get(symbol)
    if not isinstance(row, dict):
        return None
    return _normalize_commodity_quote(row)
