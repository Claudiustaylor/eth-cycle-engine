"""Sub-score functions for signal confidence."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from regimes.types import Regime


def _clip(value: float) -> float:
    return float(max(0, min(100, value)))


def _value(features: pd.DataFrame, idx: int, name: str, default: float) -> float:
    value = features.iloc[idx].get(name, default)
    if pd.isna(value):
        return default
    return float(value)


def valuation_score(features: pd.DataFrame, idx: int) -> float:
    """Score deeper drawdowns and cheap valuation higher."""

    dd = _value(features, idx, "drawdown_cycle", 0)
    score = 50 + abs(min(dd, 0)) * 70
    if "mvrv_percentile" in features:
        score += (50 - _value(features, idx, "mvrv_percentile", 50)) * 0.5
    if "realized_price_deviation" in features:
        score += -_value(features, idx, "realized_price_deviation", 0) * 20
    return _clip(score)


def trend_score(features: pd.DataFrame, idx: int) -> float:
    """Score positive moving-average structure higher."""

    score = 50
    for period, weight in [(50, 15), (200, 20)]:
        if _value(features, idx, f"price_vs_ema_{period}", 0) > 0:
            score += weight
        if _value(features, idx, f"ema_{period}_slope", 0) > 0:
            score += weight / 2
    return _clip(score)


def momentum_score(features: pd.DataFrame, idx: int) -> float:
    """Score oversold momentum with improving confirmation higher."""

    rsi = _value(features, idx, "rsi", 50)
    macd_hist = _value(features, idx, "macd_hist", 0)
    roc = _value(features, idx, "roc_14", 0)
    score = 50 + (50 - rsi) * 0.6 + (15 if macd_hist > 0 else -5) + math.tanh(roc * 10) * 10
    return _clip(score)


def volatility_score(features: pd.DataFrame, idx: int) -> float:
    """Score panic volatility that is contracting higher."""

    vol_pct = _value(features, idx, "vol_percentile", 50)
    expansion = _value(features, idx, "vol_expansion", 1)
    return _clip(45 + max(vol_pct - 50, 0) * 0.4 + max(1 - expansion, 0) * 20)


def derivatives_score(features: pd.DataFrame, idx: int) -> float:
    """Score contrarian derivatives stress; neutral when unavailable."""

    if not {"funding_rate_percentile", "liquidation_spikes"} & set(features.columns):
        return 50.0
    funding = _value(features, idx, "funding_rate_percentile", 50)
    liq = _value(features, idx, "liquidation_spikes", 0)
    return _clip(50 + (50 - funding) * 0.5 + liq * 20)


def onchain_score(features: pd.DataFrame, idx: int) -> float:
    """Score on-chain accumulation; neutral when unavailable."""

    if not {"exchange_outflow_percentile", "mvrv_percentile"} & set(features.columns):
        return 50.0
    outflow = _value(features, idx, "exchange_outflow_percentile", 50)
    mvrv = _value(features, idx, "mvrv_percentile", 50)
    return _clip(50 + (outflow - 50) * 0.4 + (50 - mvrv) * 0.5)


def macro_score(features: pd.DataFrame, idx: int) -> float:
    """Score risk-on macro conditions higher."""

    score = _value(features, idx, "risk_on_off", 50)
    if _value(features, idx, "rate_direction", 0) < 0:
        score += 10
    if _value(features, idx, "dollar_trend", 0) < 0:
        score += 10
    if _value(features, idx, "equity_trend", 0) > 0:
        score += 10
    return _clip(score)


def regime_score(features: pd.DataFrame, idx: int, regime: Regime | str | None) -> float:
    """Map regimes to opportunity scores."""

    _ = (features, idx)
    value = regime.value if isinstance(regime, Regime) else str(regime or "sideways")
    mapping = {
        "capitulation": 95,
        "accumulation": 90,
        "recovery": 75,
        "early_bull": 70,
        "bull_expansion": 60,
        "sideways": 50,
        "early_bear": 35,
        "distribution": 25,
        "late_bull": 20,
        "blow_off": 5,
    }
    return float(mapping.get(value, 50))


SUB_SCORE_FUNCS: dict[str, Any] = {
    "valuation": valuation_score,
    "trend": trend_score,
    "momentum": momentum_score,
    "volatility": volatility_score,
    "derivatives": derivatives_score,
    "onchain": onchain_score,
    "macro": macro_score,
}
