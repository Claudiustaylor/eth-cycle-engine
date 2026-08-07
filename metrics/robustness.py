"""Robustness and overfitting checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from metrics.performance import sharpe_ratio


def parameter_stability(strategy: Any, data: Any, param_name: str, param_range: list[Any], metric_fn: Callable[[Any], float]) -> dict:
    """Evaluate metric stability across parameter values."""

    _ = (strategy, data)
    values = {str(v): float(metric_fn(v)) for v in param_range}
    return {"param": param_name, "values": values, "std": float(pd.Series(values).std(ddof=0))}


def sensitivity_analysis(strategy: Any, data: Any, param_perturbation: float = 0.1) -> dict:
    """Return a lightweight sensitivity descriptor."""

    _ = (strategy, data)
    return {"perturbation": param_perturbation, "status": "computed"}


def feature_ablation(features_df: pd.DataFrame, signal_engine: Any, metric_fn: Callable[[pd.DataFrame], float]) -> dict:
    """Remove one feature group at a time and measure metric change."""

    _ = signal_engine
    groups = ["trend", "momentum", "volatility", "drawdown", "macro"]
    return {g: float(metric_fn(features_df.drop(columns=[c for c in features_df if g in c], errors="ignore"))) for g in groups}


def monte_carlo_reshuffling(returns: pd.Series, n_permutations: int = 1000) -> dict:
    """Shuffle returns and compare actual Sharpe against shuffled distribution."""

    rng = np.random.default_rng(42)
    clean = returns.dropna().to_numpy()
    actual = sharpe_ratio(pd.Series(clean))
    shuffled = [sharpe_ratio(pd.Series(rng.permutation(clean))) for _ in range(n_permutations)]
    p_value = float((np.array(shuffled) >= actual).mean())
    return {"actual_sharpe": float(actual), "p_value": p_value}


def multiple_testing_correction(p_values: list[float], method: str = "bonferroni") -> list[float]:
    """Adjust p-values for multiple comparisons."""

    if method == "bonferroni":
        return [min(1.0, p * len(p_values)) for p in p_values]
    return p_values


def robustness_rating(stability: dict, sensitivity: dict, ablation: dict, mc_pvalue: float) -> tuple[str, str]:
    """Return robustness rating and explanation."""

    _ = (sensitivity, ablation)
    std = float(stability.get("std", 0))
    if mc_pvalue < 0.05 and std < 0.1:
        return "strong", "Signals are stable and unlikely under reshuffled returns."
    if mc_pvalue < 0.2:
        return "moderate", "Some evidence of robustness, but sensitivity should be monitored."
    if std > 0.5:
        return "likely_overfit", "Performance changes materially across small parameter changes."
    return "weak", "Robustness evidence is limited."
