from __future__ import annotations

from regimes.rule_based import RuleBasedRegimeClassifier
from regimes.types import Regime


def test_capitulation_regime(synthetic_features):
    f = synthetic_features.copy()
    f.iloc[-1, f.columns.get_loc("drawdown_cycle")] = -0.5
    f.iloc[-1, f.columns.get_loc("rsi")] = 25
    f.iloc[-1, f.columns.get_loc("vol_percentile")] = 95
    assert RuleBasedRegimeClassifier({}).classify(f, len(f) - 1) == Regime.CAPITULATION


def test_classify_series_length(synthetic_features):
    series = RuleBasedRegimeClassifier({}).classify_series(synthetic_features)
    assert len(series) == len(synthetic_features)
