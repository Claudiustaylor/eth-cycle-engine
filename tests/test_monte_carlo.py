from __future__ import annotations

import pandas as pd

from simulation.monte_carlo import MonteCarloEngine


def test_bootstrap_reproducible(config):
    returns = pd.Series([0.01, -0.02, 0.03, -0.01] * 50)
    a = MonteCarloEngine(config).block_bootstrap(returns, n_sims=20, horizon=30)
    b = MonteCarloEngine(config).block_bootstrap(returns, n_sims=20, horizon=30)
    assert a == b
    assert "p50" in a


def test_regime_conditioned(config):
    returns = pd.Series([0.01, -0.02, 0.03, -0.01] * 50)
    regimes = pd.Series(["a", "b"] * 100)
    result = MonteCarloEngine(config).regime_conditioned(returns, regimes, n_sims=10, horizon=10)
    assert 0 <= result["prob_loss"] <= 1
