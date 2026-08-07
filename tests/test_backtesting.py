from __future__ import annotations

import pandas as pd

from backtesting.costs import TransactionCosts
from backtesting.engine import BacktestEngine
from regimes.rule_based import RuleBasedRegimeClassifier
from strategies.benchmarks import BuyAndHold


def test_cost_application(config):
    costs = TransactionCosts(config)
    assert costs.buy_cost(1000) > 0
    assert costs.sell_cost(1000) < 1000


def test_backtest_runs_without_future_rows(config, synthetic_ohlcv, synthetic_features):
    regimes = RuleBasedRegimeClassifier(config).classify_series(synthetic_features)
    result = BacktestEngine(BuyAndHold(), synthetic_ohlcv, synthetic_features, regimes, config).run(
        synthetic_features.index[0], synthetic_features.index[-1], 10000
    )
    assert isinstance(result.equity_curve, pd.Series)
    assert len(result.equity_curve) == len(synthetic_features)
    assert result.trades
