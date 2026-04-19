from core.filters import apply_filters
from core.scoring import calc_smooth_score
from core.metrics import calc_metrics
from models import AuctionData, AuctionTick


def test_metrics_basic():
    data = AuctionData(
        symbol="sh600703",
        name="三安光电",
        date="2026-04-20",
        prev_close=10.0,
        float_mkt_cap=1000000000,
        auction_ticks=[
            AuctionTick("09:15:00", 10.00, 100, 1000),
            AuctionTick("09:20:00", 10.01, 100, 1001),
            AuctionTick("09:25:00", 10.02, 100, 1002),
        ],
    )
    m = calc_metrics(data)
    assert m.tick_count == 3
    assert m.range_ratio is not None


def test_filter_and_score():
    data = AuctionData(
        symbol="sh600703",
        name="三安光电",
        date="2026-04-20",
        prev_close=10.0,
        float_mkt_cap=1000000,
        auction_ticks=[
            AuctionTick("09:15:00", 10.00, 1000, 10000),
            AuctionTick("09:20:00", 10.00, 1000, 10000),
            AuctionTick("09:25:00", 10.00, 1000, 10000),
        ],
    )
    m = calc_metrics(data)
    passed, reasons = apply_filters(m, {
        "max_range_ratio": 0.01,
        "max_jump_std_ratio": 0.01,
        "max_change_ratio": 1.0,
        "max_rmse_ratio": 0.01,
        "min_auction_amt_float_ratio": 0.0001,
    })
    score = calc_smooth_score(m, {
        "max_range_ratio": 0.01,
        "max_jump_std_ratio": 0.01,
        "max_change_ratio": 1.0,
        "max_rmse_ratio": 0.01,
        "min_auction_amt_float_ratio": 0.0001,
    }, {
        "range": 0.3,
        "jump_std": 0.3,
        "change_ratio": 0.2,
        "rmse": 0.2,
    })
    assert passed is True
    assert reasons == []
    assert score >= 99
