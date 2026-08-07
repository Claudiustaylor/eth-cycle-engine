"""Trend features."""

from __future__ import annotations

import pandas as pd


def compute_emas(prices: pd.Series, periods: list[int] | None = None) -> pd.DataFrame:
    """Compute exponential moving averages for configured periods."""

    periods = periods or [20, 50, 100, 200]
    return pd.DataFrame({f"ema_{p}": prices.ewm(span=p, adjust=False, min_periods=p).mean() for p in periods})


def compute_ema_slope(ema: pd.Series, window: int = 10) -> pd.Series:
    """Compute EMA slope over a trailing window."""

    return ema.pct_change(window)


def price_vs_ma(prices: pd.Series, ema: pd.Series) -> pd.Series:
    """Return price percentage distance from moving average."""

    return prices / ema - 1.0


def ma_crossovers(ema_short: pd.Series, ema_long: pd.Series) -> pd.Series:
    """Return +1 on bullish cross, -1 on bearish cross, else 0."""

    spread = ema_short - ema_long
    prev = spread.shift(1)
    return ((spread > 0) & (prev <= 0)).astype(int) - ((spread < 0) & (prev >= 0)).astype(int)
