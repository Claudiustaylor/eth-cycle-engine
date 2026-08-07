"""Drawdown features."""

from __future__ import annotations

import pandas as pd


def drawdown_from_ath(prices: pd.Series) -> pd.Series:
    """Compute drawdown from all-time high using trailing observations."""

    return prices / prices.cummax() - 1.0


def drawdown_from_cycle_high(prices: pd.Series, cycle_window: int = 252) -> pd.Series:
    """Compute drawdown from rolling cycle high."""

    return prices / prices.rolling(cycle_window, min_periods=1).max() - 1.0


def drawdown_30d(prices: pd.Series) -> pd.Series:
    """Compute drawdown from 30-day high."""

    return prices / prices.rolling(30, min_periods=1).max() - 1.0


def drawdown_90d(prices: pd.Series) -> pd.Series:
    """Compute drawdown from 90-day high."""

    return prices / prices.rolling(90, min_periods=1).max() - 1.0


def max_trailing_drawdown(prices: pd.Series, window: int = 252) -> pd.Series:
    """Compute worst trailing drawdown within each rolling window."""

    dd = prices / prices.cummax() - 1.0
    return dd.rolling(window, min_periods=1).min()
