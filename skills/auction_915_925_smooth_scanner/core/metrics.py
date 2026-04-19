import math
from typing import List

from models import AuctionData, MetricResult


def _std(values: List[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _rmse(actual: List[float], fitted: List[float]) -> float:
    if not actual or len(actual) != len(fitted):
        return 0.0
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(actual, fitted)) / len(actual))


def calc_metrics(data: AuctionData) -> MetricResult:
    prices = [x.price for x in data.auction_ticks]
    amounts = [x.amount for x in data.auction_ticks]
    prev_close = data.prev_close or 0.0
    tick_count = len(prices)

    if tick_count < 3 or prev_close <= 0:
        return MetricResult(tick_count, None, None, None, None, None, None, None, None, None, None)

    diffs = [prices[i] - prices[i - 1] for i in range(1, tick_count)]
    change_count = sum(1 for i in range(1, tick_count) if prices[i] != prices[i - 1])

    x = list(range(tick_count))
    x_mean = sum(x) / tick_count
    y_mean = sum(prices) / tick_count
    denominator = sum((xi - x_mean) ** 2 for xi in x) or 1.0
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, prices)) / denominator
    intercept = y_mean - slope * x_mean
    fitted = [slope * xi + intercept for xi in x]

    auction_amt = sum(amounts)
    return MetricResult(
        tick_count=tick_count,
        auction_open_price=prices[0],
        auction_last_price=prices[-1],
        auction_high=max(prices),
        auction_low=min(prices),
        range_ratio=(max(prices) - min(prices)) / prev_close,
        jump_std_ratio=_std(diffs) / prev_close,
        change_ratio=change_count / max(1, tick_count - 1),
        rmse_ratio=_rmse(prices, fitted) / prev_close,
        auction_amt=auction_amt,
        amt_float_ratio=(auction_amt / data.float_mkt_cap) if data.float_mkt_cap > 0 else None,
    )
