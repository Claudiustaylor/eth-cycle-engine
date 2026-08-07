from __future__ import annotations

import pandas as pd

from features.drawdown import drawdown_from_ath
from features.market_structure import breakout_detection
from features.momentum import compute_rsi
from features.trend import compute_emas


def test_feature_columns_exist(synthetic_features):
    for col in ["ema_20", "rsi", "realized_vol", "drawdown_cycle", "volume_vs_ma"]:
        assert col in synthetic_features


def test_breakout_uses_prior_high_not_current_bar():
    prices = pd.Series([1, 2, 3, 3, 4], index=pd.date_range("2020-01-01", periods=5))
    result = breakout_detection(prices, window=3)
    assert bool(result.iloc[-1])


def test_indicators_handle_insufficient_data():
    s = pd.Series([1.0, 2.0, 3.0])
    assert compute_emas(s, [5])["ema_5"].isna().all()
    assert compute_rsi(s, 14).isna().all()
    assert drawdown_from_ath(s).iloc[-1] == 0
