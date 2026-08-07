"""Monte Carlo simulation engines."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class MonteCarloEngine:
    """Run reproducible return simulations."""

    def __init__(self, config: dict[str, Any]) -> None:
        cfg = config.get("monte_carlo", config)
        self.n_simulations = int(cfg.get("n_simulations", 10000))
        self.seed = int(cfg.get("seed", 42))
        self.rng = np.random.default_rng(self.seed)

    def _report_paths(self, paths: np.ndarray, target: float = 1.0) -> dict:
        final = paths[:, -1]
        dd = paths / np.maximum.accumulate(paths, axis=1) - 1
        return {
            "p10": float(np.percentile(final, 10)),
            "p25": float(np.percentile(final, 25)),
            "p50": float(np.percentile(final, 50)),
            "p75": float(np.percentile(final, 75)),
            "p90": float(np.percentile(final, 90)),
            "prob_loss": float((final < 1).mean()),
            "prob_target": float((final >= target).mean()),
            "prob_drawdown_50": float((dd.min(axis=1) <= -0.5).mean()),
        }

    def bootstrap_resample(self, returns: pd.Series, horizon: int = 252, n_sims: int | None = None) -> dict:
        """IID bootstrap simulation."""

        n = n_sims or self.n_simulations
        clean = returns.dropna().to_numpy()
        samples = self.rng.choice(clean, size=(n, horizon), replace=True)
        return self._report_paths(np.cumprod(1 + samples, axis=1))

    def block_bootstrap(self, returns: pd.Series, block_size: int = 21, horizon: int = 252, n_sims: int | None = None) -> dict:
        """Block bootstrap preserving short autocorrelation."""

        n = n_sims or self.n_simulations
        clean = returns.dropna().to_numpy()
        if len(clean) < block_size:
            return self.bootstrap_resample(returns, horizon, n)
        starts = self.rng.integers(0, len(clean) - block_size + 1, size=(n, int(np.ceil(horizon / block_size))))
        sims = np.array([np.concatenate([clean[s : s + block_size] for s in row])[:horizon] for row in starts])
        return self._report_paths(np.cumprod(1 + sims, axis=1))

    def regime_conditioned(self, returns: pd.Series, regimes: pd.Series, horizon: int = 252, n_sims: int | None = None) -> dict:
        """Sample returns from regime-specific buckets."""

        n = n_sims or self.n_simulations
        aligned = pd.concat([returns.rename("r"), regimes.rename("regime")], axis=1).dropna()
        groups = {k: v["r"].to_numpy() for k, v in aligned.groupby("regime") if len(v)}
        labels = list(groups) or ["all"]
        if not groups:
            groups = {"all": returns.dropna().to_numpy()}
        sims = np.zeros((n, horizon))
        for i in range(n):
            for j in range(horizon):
                bucket = groups[self.rng.choice(labels)]
                sims[i, j] = self.rng.choice(bucket)
        return self._report_paths(np.cumprod(1 + sims, axis=1))

    def student_t_simulation(self, returns: pd.Series, horizon: int = 252, n_sims: int | None = None) -> dict:
        """Fit Student-t distribution and simulate returns."""

        clean = returns.dropna().to_numpy()
        df, loc, scale = stats.t.fit(clean)
        sims = stats.t.rvs(df, loc=loc, scale=scale, size=(n_sims or self.n_simulations, horizon), random_state=self.rng)
        return self._report_paths(np.cumprod(1 + sims, axis=1))

    def garch_simulation(self, returns: pd.Series, horizon: int = 252, n_sims: int | None = None) -> dict:
        """Fit GARCH(1,1) using arch when available; fall back to Student-t."""

        try:
            from arch import arch_model

            clean = returns.dropna() * 100
            model = arch_model(clean, vol="Garch", p=1, q=1, dist="t").fit(disp="off")
            sim = model.forecast(horizon=horizon, method="simulation", simulations=n_sims or self.n_simulations)
            values = np.asarray(sim.simulations.values[-1]) / 100
            return self._report_paths(np.cumprod(1 + values, axis=1))
        except Exception:
            return self.student_t_simulation(returns, horizon, n_sims)

    def report(self, simulation_results: dict) -> dict:
        """Return simulation report."""

        return simulation_results
