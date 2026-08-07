"""Run an end-to-end ETH Cycle Engine example."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from backtesting.engine import BacktestEngine
from data.ingestion import DataIngestion
from data.storage import save_parquet
from features.registry import FeatureRegistry
from metrics.performance import generate_report
from metrics.robustness import monte_carlo_reshuffling, robustness_rating
from regimes.rule_based import RuleBasedRegimeClassifier
from signals.explainability import SignalExplainer
from signals.scoring import SignalScoringEngine
from simulation.monte_carlo import MonteCarloEngine
from strategies.benchmarks import (
    BuyAndHold,
    BuyAndHoldStaked,
    DollarCostAveraging,
    MovingAverage200,
    SimpleDrawdownBuying,
)
from strategies.signal_driven import SignalDrivenStrategy


def load_config(path: str = "config/default.yaml") -> dict:
    """Load YAML configuration."""

    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    """Download data, run features, regimes, strategy, benchmarks, and reports."""

    config = load_config()
    system = config["system"]
    ingestion = DataIngestion(config)
    dataset = ingestion.fetch_all(system["data_start"], system["data_end"])
    if dataset.eth_ohlcv is None:
        raise RuntimeError("ETH data unavailable from yfinance/cache. Re-run with network access.")
    features = FeatureRegistry(dataset, config).compute().dropna(subset=["close"])
    regimes = RuleBasedRegimeClassifier(config).classify_series(features)
    strategy = SignalDrivenStrategy(config)
    result = BacktestEngine(strategy, dataset.eth_ohlcv, features, regimes, config).run(
        features.index.min(), features.index.max(), config["backtest"]["starting_capital"]
    )
    report = generate_report(result.equity_curve, result.daily_returns, result.trades)
    benchmarks = {}
    for bench in [
        BuyAndHold(),
        BuyAndHoldStaked(),
        DollarCostAveraging(),
        MovingAverage200(),
        SimpleDrawdownBuying(),
    ]:
        bt = BacktestEngine(bench, dataset.eth_ohlcv, features, regimes, config).run(
            features.index.min(), features.index.max(), config["backtest"]["starting_capital"]
        )
        benchmarks[bench.name()] = generate_report(bt.equity_curve, bt.daily_returns, bt.trades)
    mc = MonteCarloEngine({"monte_carlo": {**config["monte_carlo"], "n_simulations": 1000}})
    mc_results = mc.block_bootstrap(result.daily_returns, n_sims=1000)
    robustness = monte_carlo_reshuffling(result.daily_returns, n_permutations=100)
    rating = robustness_rating({"std": 0.0}, {}, {}, robustness["p_value"])
    scorer = SignalScoringEngine(config)
    idx = len(features) - 1
    regime = regimes.iloc[idx]
    subs = scorer.compute_sub_scores(features, idx, regime)
    score = scorer.compute_combined_score(subs)
    _, action = scorer.get_signal_band(score)
    explanation = SignalExplainer().explain(subs, score, features, idx, regime, action)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    latest = pd.DataFrame(
        {
            "equity": result.equity_curve,
            "cash": result.cash,
            "eth_holdings": result.eth_holdings,
            "staked_eth": result.staked_eth,
            "regime": regimes.reindex(result.equity_curve.index),
            "signal_score": result.signal_scores,
        }
    )
    save_parquet(latest, "latest_results")
    latest.to_parquet(out_dir / "latest_results.parquet", engine="pyarrow")
    payload = {
        "strategy": report,
        "benchmarks": benchmarks,
        "monte_carlo": mc_results,
        "robustness": {"mc": robustness, "rating": rating[0], "explanation": rating[1]},
        "latest_signal": explanation,
    }
    (out_dir / "report.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print("Strategy vs Benchmarks")
    print(pd.DataFrame({"Signal Driven": report, **benchmarks}).T.round(4))
    print("\nMonte Carlo")
    print(pd.Series(mc_results).round(4))
    print("\nRobustness")
    print(f"{rating[0]} - {rating[1]}")
    print("\nLatest Signal")
    print(explanation)
    print("\nStaking breakdown")
    print(f"Staked ETH: {result.staked_eth.iloc[-1]:.6f}")
    print("Dashboard: run `streamlit run dashboard/app.py` to explore interactively")


if __name__ == "__main__":
    main()
