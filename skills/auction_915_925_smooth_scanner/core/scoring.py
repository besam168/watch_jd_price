from models import MetricResult


def _score_upper(metric: float | None, threshold: float) -> float:
    if metric is None or threshold <= 0:
        return 0.0
    return max(0.0, 100.0 * (1.0 - metric / threshold))


def calc_smooth_score(metrics: MetricResult, thresholds: dict, weights: dict) -> float:
    score_range = _score_upper(metrics.range_ratio, thresholds["max_range_ratio"])
    score_jump = _score_upper(metrics.jump_std_ratio, thresholds["max_jump_std_ratio"])
    score_change = _score_upper(metrics.change_ratio, thresholds["max_change_ratio"])
    score_rmse = _score_upper(metrics.rmse_ratio, thresholds["max_rmse_ratio"])
    score = (
        weights["range"] * score_range
        + weights["jump_std"] * score_jump
        + weights["change_ratio"] * score_change
        + weights["rmse"] * score_rmse
    )
    return round(score, 2)
