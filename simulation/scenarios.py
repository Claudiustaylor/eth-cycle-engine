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
            horizon = min(years * 365, len(returns))
            for case in cases:
                if "bear" in case:
                    sample = returns.nsmallest(horizon)
                elif "bull" in case or "extreme" in case:
                    sample = returns.nlargest(horizon)
                else:
                    sample = returns.tail(horizon)
                # Clip to avoid overflow from compounding extreme daily returns
                compound = float((1 + sample).prod())
                compound = min(compound, 1e6)  # cap at 1Mx to prevent overflow
                out[f"{name}_{case}"] = {
                    "final_multiple": compound,
                    "label": "extreme historical replay, not expected" if case == "extreme_repeat" else case,
                }
        return out

    def format_results(self, results: dict) -> pd.DataFrame:
        """Format scenario results as a DataFrame."""

        return pd.DataFrame(results).T
