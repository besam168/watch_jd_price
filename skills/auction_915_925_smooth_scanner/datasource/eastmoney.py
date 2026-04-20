from typing import Any, Dict


def fetch(symbol: str, date: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "source": "eastmoney_pre_min",
        "symbol": symbol,
        "date": date,
        "data_granularity": "minute_agg",
        "error": "东方财富/AKShare pre-minute 路径已确认可用，但真实接线尚未写入插件",
        "raw": None,
    }
