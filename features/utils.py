"""Shared feature helpers."""

from __future__ import annotations

import pandas as pd


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Return rolling percentile rank of the current value within past/current window."""

    return series.rolling(window, min_periods=max(2, min(window, 20))).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
        raw=False,
    )
