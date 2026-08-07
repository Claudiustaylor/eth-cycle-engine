"""Optional derivatives features."""

from __future__ import annotations

import pandas as pd

from features.utils import rolling_percentile


def _none_like(input_series: pd.Series | None) -> pd.Series | None:
    return None if input_series is None else pd.Series(index=input_series.index, dtype="float64")


def funding_rate_percentile(funding: pd.Series | None, window: int = 252) -> pd.Series | None:
    """Return funding percentile or None when unavailable."""

    return None if funding is None else rolling_percentile(funding, window)


def open_interest_change(oi: pd.Series | None, window: int = 7) -> pd.Series | None:
    """Return open interest change or None when unavailable."""

    return None if oi is None else oi.pct_change(window)


def leverage_expansion(
    oi: pd.Series | None, market_cap: pd.Series | None, window: int = 14
) -> pd.Series | None:
    """Return OI/market-cap expansion or None when unavailable."""

    if oi is None or market_cap is None:
        return _none_like(oi)
    leverage = oi / market_cap
    return leverage / leverage.rolling(window, min_periods=window).mean() - 1.0


def liquidation_spikes(
    liquidations: pd.Series | None, window: int = 7, threshold: float = 3
) -> pd.Series | None:
    """Return liquidation z-score spikes or None when unavailable."""

    if liquidations is None:
        return None
    z = (liquidations - liquidations.rolling(window, min_periods=window).mean()) / liquidations.rolling(window, min_periods=window).std()
    return (z > threshold).astype(float)
