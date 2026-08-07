from __future__ import annotations

from backtesting.walk_forward import WalkForwardValidator
from strategies.benchmarks import BuyAndHold


def test_walk_forward_separates_windows(config, synthetic_ohlcv, synthetic_features):
    validator = WalkForwardValidator(BuyAndHold(), synthetic_ohlcv, synthetic_features, config)
    results = validator.run(train_years=1, test_years=1, method="rolling")
    assert isinstance(results, list)
    for result in results:
        assert result.train_period[1] < result.test_period[0]
