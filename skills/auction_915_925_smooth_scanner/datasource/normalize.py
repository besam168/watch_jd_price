from typing import Any, Dict, List

from models import AuctionData, AuctionTick
from datasource.helpers import in_auction_window


def normalize_payload(payload: Dict[str, Any], symbol: str, date: str) -> AuctionData | None:
    if not payload or not payload.get("ok"):
        return None

    raw = payload.get("raw") or {}
    ticks_raw: List[Dict[str, Any]] = raw.get("auction_ticks") or []
    prev_close = float(raw.get("prev_close") or 0)
    float_mkt_cap = float(raw.get("float_mkt_cap") or 0)
    name = str(raw.get("name") or symbol)

    dedup = {}
    for item in ticks_raw:
        ts = str(item.get("time") or "")
        if not in_auction_window(ts):
            continue
        price = item.get("price")
        if price in (None, "", "--"):
            continue
        key = ts
        current = {
            "time": ts,
            "price": float(price),
            "volume": float(item.get("volume") or 0),
            "amount": float(item.get("amount") or 0),
        }
        old = dedup.get(key)
        if old is None or current["amount"] >= old["amount"]:
            dedup[key] = current

    ticks = [AuctionTick(**v) for _, v in sorted(dedup.items(), key=lambda x: x[0])]
    if len(ticks) < 3:
        return None

    return AuctionData(
        symbol=symbol,
        name=name,
        date=date,
        prev_close=prev_close,
        float_mkt_cap=float_mkt_cap,
        auction_ticks=ticks,
        source=str(payload.get("source") or ""),
        data_granularity=str(payload.get("data_granularity") or "unknown"),
        raw_meta={"payload_source": payload.get("source")},
    )
