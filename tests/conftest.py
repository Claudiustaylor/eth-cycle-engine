from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.schemas import DataSet
from features.registry import FeatureRegistry


@pytest.fixture
def config(tmp_path):
    return {
        "data": {
            "sources": {},
            "cache": {"path": str(tmp_path), "max_age_hours": 24},
        },
        "features": {
            "trend": {"enabled": True, "ema_periods": [20, 50, 100, 200]},
            "momentum": {"enabled": True, "rsi_period": 14, "macd": [12, 26, 9]},
            "volatility": {"enabled": True, "rv_window": 21},
            "drawdown": {"enabled": True, "cycle_window": 252},
            "volume": {"enabled": True},
            "market_structure": {"enabled": True, "structure_window": 20},
            "macro": {"enabled": True},
            "derivatives": {"enabled": False},
            "onchain": {"enabled": False},
        },
        "signals": {"weights": {"valuation": 0.2, "trend": 0.15, "momentum": 0.15, "volatility": 0.1, "derivatives": 0.1, "onchain": 0.1, "macro": 0.1, "regime": 0.1}},
        "position_sizing": {"tranches": {"buy": {60: 0.1, 70: 0.15, 80: 0.25, 90: 0.3}, "sell": {40: 0.2, 20: 0.4}}, "drawdown_buying": {"method": "increasing", "thresholds": [-0.1, -0.2, -0.3], "require_regime_confirmation": True}},
        "risk": {"max_exposure": 0.95, "min_cash_reserve": 0.05, "anomaly": {"return_zscore_threshold": 4, "vol_percentile_threshold": 95, "volume_spike_multiple": 5, "defensive_reduction": 0.5}},
        "staking": {"enabled": True, "annual_yield": 0.03, "compounding_frequency": "daily", "pct_staked": 1.0, "lockup_days": 0, "slashing_risk": 0.0},
        "transaction_costs": {"trading_fee_pct": 0.001, "spread_pct": 0.0005, "slippage_pct": 0.001},
        "monte_carlo": {"n_simulations": 100, "seed": 42},
    }


@pytest.fixture
def synthetic_ohlcv():
    rng = np.random.default_rng(42)
    idx = pd.date_range("2020-01-01", periods=420, freq="D")
    close = pd.Series(1000 * np.cumprod(1 + rng.normal(0.001, 0.03, len(idx))), index=idx)
    return pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.03,
            "low": close * 0.97,
            "close": close,
            "volume": 1_000_000 + rng.normal(0, 100_000, len(idx)).clip(-300_000, 300_000),
        },
        index=idx,
    )


@pytest.fixture
def synthetic_features(synthetic_ohlcv, config):
    btc = synthetic_ohlcv.copy()
    btc["close"] *= 20
    macro = pd.DataFrame({"sp500": np.linspace(3000, 4200, len(synthetic_ohlcv)), "dxy": np.linspace(105, 95, len(synthetic_ohlcv)), "treasury_2y": np.linspace(5, 3, len(synthetic_ohlcv))}, index=synthetic_ohlcv.index)
    return FeatureRegistry(DataSet(eth_ohlcv=synthetic_ohlcv, btc_ohlcv=btc, macro=macro), config).compute()
