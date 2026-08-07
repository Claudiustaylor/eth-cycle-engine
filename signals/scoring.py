"""Combined signal scoring engine."""

from __future__ import annotations

from typing import Any

import pandas as pd

from regimes.types import Regime
from signals.sub_scores import SUB_SCORE_FUNCS, regime_score


class SignalScoringEngine:
    """Compute 0-100 signal scores from explainable sub-scores."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.weights = config.get("signals", {}).get(
            "weights",
            {
                "valuation": 0.20,
                "trend": 0.15,
                "momentum": 0.15,
                "volatility": 0.10,
                "derivatives": 0.10,
                "onchain": 0.10,
                "macro": 0.10,
                "regime": 0.10,
            },
        )

    def compute_sub_scores(
        self, features_df: pd.DataFrame, idx: int, regime: Regime | str | None = None
    ) -> dict[str, float]:
        """Return sub-scores for a row."""

        scores = {name: func(features_df, idx) for name, func in SUB_SCORE_FUNCS.items()}
        scores["regime"] = regime_score(features_df, idx, regime)
        return scores

    def compute_combined_score(self, sub_scores: dict[str, float]) -> float:
        """Return weighted 0-100 combined score."""

        weight_sum = sum(self.weights.get(k, 0) for k in sub_scores)
        if weight_sum <= 0:
            return 50.0
        return float(
            max(0, min(100, sum(sub_scores[k] * self.weights.get(k, 0) for k in sub_scores) / weight_sum))
        )

    def get_signal_band(self, score: float) -> tuple[str, str]:
        """Return band name and action text for a score."""

        if score <= 20:
            return ("strong_sell", "extreme caution")
        if score <= 40:
            return ("reduce", "reduce exposure")
        if score <= 59:
            return ("neutral", "neutral")
        if score <= 74:
            return ("accumulate", "initial accumulation")
        if score <= 89:
            return ("strong_accumulate", "strong accumulation")
        return ("extreme_accumulate", "extreme accumulation opportunity")
