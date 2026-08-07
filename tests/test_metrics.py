from __future__ import annotations

import pandas as pd

from metrics.performance import cagr, max_drawdown, sharpe_ratio
from metrics.risk import conditional_var, value_at_risk


def test_known_metrics():
    equity = pd.Series([100, 110, 90, 120], index=pd.date_range("2020-01-01", periods=4))
    returns = equity.pct_change().fillna(0)
    assert max_drawdown(equity) < 0
    assert cagr(equity) > 0
    assert isinstance(sharpe_ratio(returns), float)
    assert value_at_risk(returns) <= 0
    assert conditional_var(returns) <= 0
