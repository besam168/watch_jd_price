from dataclasses import dataclass, field
from typing import List


DEFAULT_THRESHOLDS = {
    "max_range_ratio": 0.004,
    "max_jump_std_ratio": 0.0015,
    "max_change_ratio": 0.35,
    "max_rmse_ratio": 0.0018,
    "min_auction_amt_float_ratio": 0.0003,
}

DEFAULT_SCORING_WEIGHTS = {
    "range": 0.30,
    "jump_std": 0.30,
    "change_ratio": 0.20,
    "rmse": 0.20,
}


@dataclass
class RuntimeConfig:
    failover_enabled: bool = True
    save_raw: bool = True
    log_level: str = "INFO"


@dataclass
class ScanConfig:
    date: str = "auto_today"
    market: List[str] = field(default_factory=lambda: ["SH", "SZ"])
    universe_mode: str = "all_a"
    custom_symbols: List[str] = field(default_factory=list)
    top_n: int = 100
    thresholds: dict = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))
    scoring_weights: dict = field(default_factory=lambda: dict(DEFAULT_SCORING_WEIGHTS))
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
