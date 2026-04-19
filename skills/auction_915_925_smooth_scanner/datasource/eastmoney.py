from typing import Any, Dict


def fetch(symbol: str, date: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "source": "eastmoney",
        "symbol": symbol,
        "date": date,
        "data_granularity": "unknown",
        "error": "东方财富竞价接口待接入",
        "raw": None,
    }
