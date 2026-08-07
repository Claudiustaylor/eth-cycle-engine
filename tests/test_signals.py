from __future__ import annotations

from regimes.types import Regime
from signals.explainability import SignalExplainer
from signals.scoring import SignalScoringEngine


def test_score_ranges_and_bands(config, synthetic_features):
    engine = SignalScoringEngine(config)
    subs = engine.compute_sub_scores(synthetic_features, len(synthetic_features) - 1, Regime.ACCUMULATION)
    assert all(0 <= v <= 100 for v in subs.values())
    assert engine.get_signal_band(20)[0] == "strong_sell"
    assert engine.get_signal_band(90)[0] == "extreme_accumulate"


def test_explanation_contains_values(config, synthetic_features):
    engine = SignalScoringEngine(config)
    idx = len(synthetic_features) - 1
    subs = engine.compute_sub_scores(synthetic_features, idx, Regime.ACCUMULATION)
    score = engine.compute_combined_score(subs)
    text = SignalExplainer().explain(subs, score, synthetic_features, idx, Regime.ACCUMULATION, "test action")
    assert "SIGNAL CONFIDENCE" in text
    assert "SUB-SCORES" in text
