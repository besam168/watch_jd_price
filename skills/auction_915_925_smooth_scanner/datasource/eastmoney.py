from __future__ import annotations

from typing import Any, Dict, List

import akshare as ak


def _to_market_prefix(symbol: str) -> str:
    s = symbol.lower().strip()
    if s.startswith(("sz", "sh")):
        return s[2:]
    return s


def _normalize_rows(df) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if df is None or getattr(df, "empty", True):
        return rows

    rename_map = {
        "时间": "time",
        "日期时间": "time",
        "成交价": "price",
        "价格": "price",
        "开盘": "price",
        "成交量": "volume",
        "成交额": "amount",
    }
    cols = [rename_map.get(str(c), str(c)) for c in list(df.columns)]
    df = df.copy()
    df.columns = cols

    for _, row in df.iterrows():
        ts = str(row.get("time") or "")
        if " " in ts:
            ts = ts.split(" ")[-1]
        rows.append(
            {
                "time": ts,
                "price": row.get("price"),
                "volume": row.get("volume") or 0,
                "amount": row.get("amount") or 0,
            }
        )
    return rows


def fetch(symbol: str, date: str) -> Dict[str, Any]:
    code = _to_market_prefix(symbol)
    last_error = None
    for _ in range(2):
        try:
            df = ak.stock_zh_a_hist_pre_min_em(
                symbol=code,
                start_time="09:15:00",
                end_time="09:25:00",
            )
            ticks = _normalize_rows(df)
            if not ticks:
                return {
                    "ok": False,
                    "source": "eastmoney_pre_min",
                    "symbol": symbol,
                    "date": date,
                    "data_granularity": "minute_agg",
                    "error": "empty_pre_min_data",
                    "raw": None,
                }
            last_price = None
            try:
                last_price = float(ticks[-1]["price"])
            except Exception:
                last_price = 0.0
            return {
                "ok": True,
                "source": "eastmoney_pre_min",
                "symbol": symbol,
                "date": date,
                "data_granularity": "minute_agg",
                "error": None,
                "raw": {
                    "name": symbol,
                    "prev_close": last_price,
                    "float_mkt_cap": 0,
                    "auction_ticks": ticks,
                },
            }
        except Exception as e:
            last_error = str(e)
    return {
        "ok": False,
        "source": "eastmoney_pre_min",
        "symbol": symbol,
        "date": date,
        "data_granularity": "minute_agg",
        "error": f"eastmoney_pre_min_failed: {last_error}",
        "raw": None,
    }
