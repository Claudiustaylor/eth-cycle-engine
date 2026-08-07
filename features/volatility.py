"""Volatility features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.utils import rolling_percentile


def compute_atr(highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> pd.Series:
    """Compute average true range."""

    prev_close = closes.shift(1)
    tr = pd.concat([(highs - lows), (highs - prev_close).abs(), (lows - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def realized_volatility(returns: pd.Series, window: int = 21) -> pd.Series:
    """Compute annualized trailing realized volatility."""

    return returns.rolling(window, min_periods=window).std() * np.sqrt(365)


def bollinger_band_width(closes: pd.Series, window: int = 20, num_std: float = 2) -> pd.Series:
    """Compute Bollinger band width as a percentage of mean."""

    mean = closes.rolling(window, min_periods=window).mean()
    std = closes.rolling(window, min_periods=window).std()
    return (2 * num_std * std) / mean


def volatility_percentile(realized_vol: pd.Series, window: int = 252) -> pd.Series:
    """Compute rolling percentile of realized volatility."""

    return rolling_percentile(realized_vol, window)


def volatility_expansion(rv_short: pd.Series, rv_long: pd.Series) -> pd.Series:
    """Compute short/long volatility ratio."""

    return rv_short / rv_long
