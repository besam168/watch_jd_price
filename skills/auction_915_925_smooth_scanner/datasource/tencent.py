from dataclasses import asdict
from typing import Any, Dict


def fetch(symbol: str, date: str) -> Dict[str, Any]:
    """腾讯主源占位实现。

    这里先返回统一包络，后续再接真实接口。
    """
    return {
        "ok": False,
        "source": "tencent",
        "symbol": symbol,
        "date": date,
        "data_granularity": "unknown",
        "error": "腾讯竞价接口待接入",
        "raw": None,
    }
