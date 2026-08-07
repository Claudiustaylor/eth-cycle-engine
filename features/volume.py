"""Volume features."""

from __future__ import annotations

import pandas as pd


def volume_vs_ma(volume: pd.Series, window: int = 20) -> pd.Series:
    """Compute volume relative to trailing moving average."""

    return volume / volume.rolling(window, min_periods=window).mean()


def volume_acceleration(volume: pd.Series, window: int = 10) -> pd.Series:
    """Compute trailing volume rate of change."""

    return volume.pct_change(window)


def price_volume_divergence(prices: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
    """Return 1 for bearish price-up volume-down divergence, -1 for bullish divergence."""

    price_trend = prices.pct_change(window)
    vol_trend = volume.pct_change(window)
    return ((price_trend > 0) & (vol_trend < 0)).astype(int) - ((price_trend < 0) & (vol_trend > 0)).astype(int)
