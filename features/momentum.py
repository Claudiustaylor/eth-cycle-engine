"""Momentum features."""

from __future__ import annotations

import pandas as pd

from features.utils import rolling_percentile


def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute Wilder RSI."""

    delta = prices.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def compute_macd(
    prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """Compute MACD line, signal line, and histogram."""

    fast_ema = prices.ewm(span=fast, adjust=False, min_periods=fast).mean()
    slow_ema = prices.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd = fast_ema - slow_ema
    signal_line = macd.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return pd.DataFrame({"macd": macd, "macd_signal": signal_line, "macd_hist": macd - signal_line})


def rate_of_change(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute trailing rate of change."""

    return prices.pct_change(period)


def momentum_percentile(prices: pd.Series, indicator: pd.Series, window: int = 252) -> pd.Series:
    """Compute rolling percentile for a momentum indicator."""

    _ = prices
    return rolling_percentile(indicator, window)


def relative_strength_vs_btc(
    eth_prices: pd.Series, btc_prices: pd.Series, window: int = 90
) -> pd.Series:
    """Compute ETH/BTC relative strength normalized to the trailing window."""

    ratio = eth_prices / btc_prices
    return ratio / ratio.rolling(window, min_periods=window).mean() - 1.0
