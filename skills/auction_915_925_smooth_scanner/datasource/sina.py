from typing import Any, Dict


def fetch(symbol: str, date: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "source": "sina",
        "symbol": symbol,
        "date": date,
        "data_granularity": "unknown",
        "error": "新浪竞价接口待接入",
        "raw": None,
    }
