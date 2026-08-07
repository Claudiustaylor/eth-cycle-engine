"""Risk metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical value at risk."""

    return float(np.quantile(returns.dropna(), 1 - confidence)) if len(returns.dropna()) else 0.0


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical conditional value at risk."""

    var = value_at_risk(returns, confidence)
    tail = returns.dropna()[returns.dropna() <= var]
    return float(tail.mean()) if len(tail) else 0.0


def downside_deviation(returns: pd.Series, mar: float = 0) -> float:
    """Downside deviation."""

    downside = returns[returns < mar]
    return float(np.sqrt(((downside - mar) ** 2).mean())) if len(downside) else 0.0


def ulcer_index(equity_curve: pd.Series) -> float:
    """Ulcer index from percentage drawdowns."""

    dd = (equity_curve / equity_curve.cummax() - 1) * 100
    return float(np.sqrt((dd**2).mean())) if len(dd) else 0.0
