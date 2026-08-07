"""Scenario analysis."""

from __future__ import annotations

from typing import Any

import pandas as pd


class ScenarioAnalyzer:
    """Construct labeled historical scenario summaries."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def run_scenarios(self, strategy: Any, data: pd.DataFrame, periods: dict[str, int]) -> dict:
        """Run labeled scenarios from historical return samples."""

        _ = strategy
        returns = data["close"].pct_change().dropna()
        cases = ["severe_bear", "bear_base", "historical_cycle", "moderate_bull", "strong_bull", "extreme_repeat"]
        out: dict[str, dict[str, float | str]] = {}
        for name, years in periods.items():
            horizon = years * 365
            for case in cases:
                sample = returns.nsmallest(min(horizon, len(returns))) if "bear" in case else returns.nlargest(min(horizon, len(returns))) if "bull" in case or "extreme" in case else returns.tail(min(horizon, len(returns)))
                out[f"{name}_{case}"] = {"final_multiple": float((1 + sample).prod()), "label": "extreme historical replay, not expected" if case == "extreme_repeat" else case}
        return out

    def format_results(self, results: dict) -> pd.DataFrame:
        """Format scenario results as a DataFrame."""

        return pd.DataFrame(results).T
