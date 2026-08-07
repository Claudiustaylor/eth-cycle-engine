"""Walk-forward validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from backtesting.engine import BacktestEngine
from metrics.performance import generate_report
from regimes.rule_based import RuleBasedRegimeClassifier
from strategies.base import Strategy


@dataclass
class WalkForwardResult:
    """Single walk-forward window result."""

    train_metrics: dict[str, float]
    test_metrics: dict[str, float]
    train_period: tuple[pd.Timestamp, pd.Timestamp]
    test_period: tuple[pd.Timestamp, pd.Timestamp]


class WalkForwardValidator:
    """Run expanding or rolling walk-forward windows."""

    def __init__(self, strategy: Strategy, data: pd.DataFrame, features: pd.DataFrame, config: dict[str, Any]) -> None:
        self.strategy = strategy
        self.data = data
        self.features = features
        self.config = config

    def run(self, train_years: int = 3, test_years: int = 1, method: str = "expanding") -> list[WalkForwardResult]:
        """Return walk-forward train/test metrics."""

        dates = self.features.index
        start = dates.min()
        end = dates.max()
        results: list[WalkForwardResult] = []
        cursor = start + pd.DateOffset(years=train_years)
        classifier = RuleBasedRegimeClassifier(self.config)
        regimes = classifier.classify_series(self.features)
        while cursor + pd.DateOffset(years=test_years) <= end:
            train_start = start if method == "expanding" else cursor - pd.DateOffset(years=train_years)
            train_end = cursor - pd.Timedelta(days=1)
            test_start = cursor
            test_end = cursor + pd.DateOffset(years=test_years) - pd.Timedelta(days=1)
            train_bt = BacktestEngine(self.strategy, self.data, self.features, regimes, self.config).run(train_start, train_end)
            test_bt = BacktestEngine(self.strategy, self.data, self.features, regimes, self.config).run(test_start, test_end)
            results.append(
                WalkForwardResult(
                    generate_report(train_bt.equity_curve, train_bt.daily_returns, train_bt.trades),
                    generate_report(test_bt.equity_curve, test_bt.daily_returns, test_bt.trades),
                    (pd.Timestamp(train_start), pd.Timestamp(train_end)),
                    (pd.Timestamp(test_start), pd.Timestamp(test_end)),
                )
            )
            cursor += pd.DateOffset(years=test_years)
        return results

    def compare_windows(self, results: list[WalkForwardResult]) -> dict[str, float]:
        """Report stability of test returns across windows."""

        vals = [r.test_metrics.get("total_return", 0.0) for r in results]
        s = pd.Series(vals, dtype="float64")
        return {"windows": float(len(results)), "mean_return": float(s.mean() if len(s) else 0), "std_return": float(s.std(ddof=0) if len(s) else 0)}
