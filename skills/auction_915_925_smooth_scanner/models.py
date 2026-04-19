from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AuctionTick:
    time: str
    price: float
    volume: float = 0.0
    amount: float = 0.0


@dataclass
class AuctionData:
    symbol: str
    name: str
    date: str
    prev_close: float
    float_mkt_cap: float
    auction_ticks: List[AuctionTick] = field(default_factory=list)
    source: str = ""
    data_granularity: str = "unknown"
    raw_meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricResult:
    tick_count: int
    auction_open_price: Optional[float]
    auction_last_price: Optional[float]
    auction_high: Optional[float]
    auction_low: Optional[float]
    range_ratio: Optional[float]
    jump_std_ratio: Optional[float]
    change_ratio: Optional[float]
    rmse_ratio: Optional[float]
    auction_amt: Optional[float]
    amt_float_ratio: Optional[float]
