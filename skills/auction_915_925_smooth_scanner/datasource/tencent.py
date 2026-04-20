from __future__ import annotations

from typing import Any, Dict, List

import akshare as ak


def _normalize_symbol(symbol: str) -> str:
    s = symbol.lower().strip()
    if s.startswith(("sz", "sh")):
        return s
    if s.startswith(("00", "001", "002", "003")):
        return f"sz{s}"
    return f"sh{s}"


def _decode_col(text: str) -> str:
    try:
        return str(text).encode("latin1", errors="ignore").decode("gbk", errors="ignore") or str(text)
    except Exception:
        return str(text)


def _rename_columns(df):
    mapping = {}
    for col in list(df.columns):
        dc = _decode_col(col)
        if "时间" in dc:
            mapping[col] = "time"
        elif "成交价格" in dc or dc == "价格":
            mapping[col] = "price"
        elif "成交量" in dc:
            mapping[col] = "volume"
        elif "成交金额" in dc:
            mapping[col] = "amount"
        else:
            mapping[col] = dc
    return df.rename(columns=mapping)


def _in_window(ts: str) -> bool:
    return "09:15:00" <= ts <= "09:25:00"


def fetch(symbol: str, date: str) -> Dict[str, Any]:
    code = _normalize_symbol(symbol)
    try:
        df = ak.stock_zh_a_tick_tx_js(symbol=code)
        if df is None or getattr(df, "empty", True):
            return {
                "ok": False,
                "source": "tencent_tick_tx",
                "symbol": symbol,
                "date": date,
                "data_granularity": "tick",
                "error": "empty_tick_data",
                "raw": None,
            }
        df = _rename_columns(df)
        ticks: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            ts = str(row.get("time") or "")
            if not _in_window(ts):
                continue
            price = row.get("price")
            if price in (None, "", "--"):
                continue
            ticks.append(
                {
                    "time": ts,
                    "price": price,
                    "volume": row.get("volume") or 0,
                    "amount": row.get("amount") or 0,
                }
            )
        if len(ticks) < 1:
            return {
                "ok": False,
                "source": "tencent_tick_tx",
                "symbol": symbol,
                "date": date,
                "data_granularity": "tick",
                "error": "no_ticks_in_0915_0925_window",
                "raw": None,
            }
        prev_close = 0.0
        try:
            prev_close = float(ticks[-1]["price"])
        except Exception:
            prev_close = 0.0
        return {
            "ok": True,
            "source": "tencent_tick_tx",
            "symbol": symbol,
            "date": date,
            "data_granularity": "tick",
            "error": None,
            "raw": {
                "name": symbol,
                "prev_close": prev_close,
                "float_mkt_cap": 0,
                "auction_ticks": ticks,
            },
        }
    except Exception as e:
        return {
            "ok": False,
            "source": "tencent_tick_tx",
            "symbol": symbol,
            "date": date,
            "data_granularity": "tick",
            "error": f"tencent_tick_failed: {e}",
            "raw": None,
        }
