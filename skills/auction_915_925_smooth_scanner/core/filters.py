from models import MetricResult


def apply_filters(metrics: MetricResult, thresholds: dict) -> tuple[bool, list[str]]:
    reasons = []
    if metrics.tick_count < 3:
        reasons.append("insufficient_ticks")
    if metrics.range_ratio is None or metrics.range_ratio > thresholds["max_range_ratio"]:
        reasons.append("range_ratio_exceeded")
    if metrics.jump_std_ratio is None or metrics.jump_std_ratio > thresholds["max_jump_std_ratio"]:
        reasons.append("jump_std_ratio_exceeded")
    if metrics.change_ratio is None or metrics.change_ratio > thresholds["max_change_ratio"]:
        reasons.append("change_ratio_exceeded")
    if metrics.rmse_ratio is None or metrics.rmse_ratio > thresholds["max_rmse_ratio"]:
        reasons.append("rmse_ratio_exceeded")
    if metrics.amt_float_ratio is None or metrics.amt_float_ratio < thresholds["min_auction_amt_float_ratio"]:
        reasons.append("amt_float_ratio_too_low")
    return (len(reasons) == 0, reasons)
