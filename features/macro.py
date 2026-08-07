"""Macro risk features."""

from __future__ import annotations

import pandas as pd


def risk_on_risk_off(
    sp500: pd.Series, dxy: pd.Series, vix_proxy: pd.Series | None = None, window: int = 20
) -> pd.Series:
    """Composite risk score from equity trend, dollar trend, and optional volatility proxy."""

    equity = sp500.pct_change(window)
    dollar = -dxy.pct_change(window)
    score = equity.rank(pct=True) * 50 + dollar.rank(pct=True) * 50
    if vix_proxy is not None:
        score = score - vix_proxy.pct_change(window).rank(pct=True) * 20
    return score.clip(0, 100)


def rate_direction(treasury_2y: pd.Series, window: int = 20) -> pd.Series:
    """Return trailing slope of two-year yields."""

    return treasury_2y.diff(window)


def dollar_strength_trend(dxy: pd.Series, window: int = 20) -> pd.Series:
    """Return trailing DXY percentage change."""

    return dxy.pct_change(window)


def equity_market_trend(sp500: pd.Series, window: int = 50) -> pd.Series:
    """Return 1 when S&P 500 is above its trailing moving average, else 0."""

    return (sp500 > sp500.rolling(window, min_periods=window).mean()).astype(float)
