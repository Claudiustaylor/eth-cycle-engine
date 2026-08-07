"""Market structure features."""

from __future__ import annotations

import pandas as pd


def higher_highs_higher_lows(prices: pd.Series, window: int = 20) -> pd.DataFrame:
    """Detect higher-high/higher-low conditions and streak length."""

    highs = prices.rolling(window, min_periods=window).max()
    lows = prices.rolling(window, min_periods=window).min()
    cond = (highs > highs.shift(window)) & (lows > lows.shift(window))
    streak = cond.groupby((cond != cond.shift()).cumsum()).cumcount().add(1).where(cond, 0)
    return pd.DataFrame({"hh_hl": cond, "hh_hl_streak": streak})


def lower_highs_lower_lows(prices: pd.Series, window: int = 20) -> pd.DataFrame:
    """Detect lower-high/lower-low conditions and streak length."""

    highs = prices.rolling(window, min_periods=window).max()
    lows = prices.rolling(window, min_periods=window).min()
    cond = (highs < highs.shift(window)) & (lows < lows.shift(window))
    streak = cond.groupby((cond != cond.shift()).cumsum()).cumcount().add(1).where(cond, 0)
    return pd.DataFrame({"lh_ll": cond, "lh_ll_streak": streak})


def distance_from_local_high(prices: pd.Series, window: int = 20) -> pd.Series:
    """Return percentage below trailing local high."""

    return prices / prices.rolling(window, min_periods=1).max() - 1.0


def distance_from_local_low(prices: pd.Series, window: int = 20) -> pd.Series:
    """Return percentage above trailing local low."""

    return prices / prices.rolling(window, min_periods=1).min() - 1.0


def breakout_detection(prices: pd.Series, window: int = 20) -> pd.Series:
    """Detect close above prior local high."""

    return prices > prices.shift(1).rolling(window, min_periods=window).max()


def failed_breakout_detection(prices: pd.Series, window: int = 20, lookback: int = 5) -> pd.Series:
    """Detect recent breakout followed by a close back under prior local high."""

    breakout = breakout_detection(prices, window)
    prior_high = prices.shift(1).rolling(window, min_periods=window).max()
    return breakout.rolling(lookback, min_periods=1).max().astype(bool) & (prices < prior_high)
