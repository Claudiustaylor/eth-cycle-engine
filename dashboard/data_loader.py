"""Shared data loader for dashboard pages — auto-downloads if cache is missing."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from data.ingestion import DataIngestion
from data.storage import load_parquet, save_parquet
from features.registry import FeatureRegistry
from regimes.rule_based import RuleBasedRegimeClassifier

logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_config() -> dict:
    """Load config, creating a minimal one if missing."""

    config_path = Path("config/default.yaml")
    if config_path.exists():
        with open(config_path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    # Minimal fallback config
    return {
        "system": {"data_start": "2017-11-01", "data_end": "2024-12-31", "random_seed": 42},
        "data": {
            "sources": {
                "eth_ohlcv": {"enabled": True, "provider": "yfinance"},
                "btc_ohlcv": {"enabled": True, "provider": "yfinance"},
                "macro": {"enabled": True, "provider": "yfinance"},
                "onchain": {"enabled": False, "provider": "none"},
                "derivatives": {"enabled": False, "provider": "none"},
                "staking": {"enabled": False, "provider": "config", "default_yield": 0.03},
            },
            "cache": {"max_age_hours": 99999, "path": "data/parquet/"},
        },
        "features": {
            "trend": {"enabled": True, "ema_periods": [20, 50, 100, 200]},
            "momentum": {"enabled": True, "rsi_period": 14, "macd": [12, 26, 9]},
            "volatility": {"enabled": True, "atr_period": 14, "rv_window": 21},
            "drawdown": {"enabled": True, "cycle_window": 252},
            "volume": {"enabled": True, "volume_ma": 20},
            "market_structure": {"enabled": True, "structure_window": 20},
            "derivatives": {"enabled": False},
            "onchain": {"enabled": False},
            "macro": {"enabled": True},
        },
        "regimes": {"method": "rule_based", "ml_method": None},
        "signals": {
            "weights": {
                "valuation": 0.20, "trend": 0.15, "momentum": 0.15,
                "volatility": 0.10, "derivatives": 0.10, "onchain": 0.10,
                "macro": 0.10, "regime": 0.10,
            },
        },
        "position_sizing": {
            "method": "tranche",
            "tranches": {"buy": {"60": 0.10, "70": 0.15, "80": 0.25, "90": 0.30}, "sell": {"40": 0.20, "20": 0.40}},
            "drawdown_buying": {
                "method": "increasing",
                "thresholds": [-0.10, -0.20, -0.30, -0.40, -0.50, -0.60, -0.70, -0.80],
                "require_regime_confirmation": True,
                "require_trend_confirmation": False,
            },
        },
        "risk": {
            "max_exposure": 0.95, "min_cash_reserve": 0.05, "max_drawdown_stop": 0.60,
            "anomaly": {"return_zscore_threshold": 4.0, "vol_percentile_threshold": 95, "volume_spike_multiple": 5.0, "defensive_reduction": 0.50},
        },
        "staking": {"enabled": True, "annual_yield": 0.03, "validator_fee": 0.0, "compounding_frequency": "daily", "pct_staked": 1.0, "lockup_days": 0, "slashing_risk": 0.0},
        "transaction_costs": {"trading_fee_pct": 0.001, "spread_pct": 0.0005, "slippage_pct": 0.001, "staking_fee_pct": 0.0, "withdrawal_fee": 0.0},
        "tax": {"enabled": False, "mode": "none"},
        "backtest": {"starting_capital": 50000},
        "monte_carlo": {"n_simulations": 1000, "horizon_days": 252, "seed": 42},
        "scenarios": {"periods": {"4yr": 4, "5yr": 5, "10yr": 10}},
        "overfitting": {"param_perturbation": 0.10, "mc_permutations": 500, "significance_level": 0.05},
    }


@st.cache_data(show_spinner="Downloading ETH data from yfinance (this takes ~30 seconds on first load)...")
def ensure_data() -> bool:
    """Download all data if cache is missing. Returns True on success."""

    config = get_config()
    system = config["system"]
    ingestion = DataIngestion(config)
    dataset = ingestion.fetch_all(system["data_start"], system["data_end"])
    if dataset.eth_ohlcv is None:
        return False
    # Compute and cache features + regimes + backtest results
    try:
        features = FeatureRegistry(dataset, config).compute().dropna(subset=["close"])
        regimes = RuleBasedRegimeClassifier(config).classify_series(features)

        from backtesting.engine import BacktestEngine
        from metrics.performance import generate_report
        from strategies.signal_driven import SignalDrivenStrategy
        from strategies.benchmarks import (
            BuyAndHold, BuyAndHoldStaked, DollarCostAveraging,
            MovingAverage200, SimpleDrawdownBuying,
        )

        strategy = SignalDrivenStrategy(config)
        result = BacktestEngine(strategy, dataset.eth_ohlcv, features, regimes, config).run(
            features.index.min(), features.index.max(), config["backtest"]["starting_capital"]
        )

        # Save combined results for dashboard pages
        latest = pd.DataFrame({
            "equity": result.equity_curve,
            "cash": result.cash,
            "eth_holdings": result.eth_holdings,
            "staked_eth": result.staked_eth,
            "regime": regimes.reindex(result.equity_curve.index),
            "signal_score": result.signal_scores,
        })
        save_parquet(latest, "latest_results")

        # Save benchmarks + report JSON
        import json
        report = generate_report(result.equity_curve, result.daily_returns, result.trades)
        benchmarks = {}
        for bench_cls in [BuyAndHold, BuyAndHoldStaked, DollarCostAveraging, MovingAverage200, SimpleDrawdownBuying]:
            bench = bench_cls()
            bt = BacktestEngine(bench, dataset.eth_ohlcv, features, regimes, config).run(
                features.index.min(), features.index.max(), config["backtest"]["starting_capital"]
            )
            benchmarks[bench.name()] = generate_report(bt.equity_curve, bt.daily_returns, bt.trades)

        from metrics.robustness import monte_carlo_reshuffling, robustness_rating
        from simulation.monte_carlo import MonteCarloEngine
        mc = MonteCarloEngine({"monte_carlo": {**config["monte_carlo"], "n_simulations": 500}})
        mc_results = mc.block_bootstrap(result.daily_returns, n_sims=500)
        robustness = monte_carlo_reshuffling(result.daily_returns, n_permutations=200)
        rating = robustness_rating({"std": 0.0}, {}, {}, robustness["p_value"])

        from signals.scoring import SignalScoringEngine
        from signals.explainability import SignalExplainer
        scorer = SignalScoringEngine(config)
        idx = len(features) - 1
        regime_val = regimes.iloc[idx]
        subs = scorer.compute_sub_scores(features, idx, regime_val)
        score = scorer.compute_combined_score(subs)
        _, action = scorer.get_signal_band(score)
        explanation = SignalExplainer().explain(subs, score, features, idx, regime_val, action)

        payload = {
            "strategy": report,
            "benchmarks": benchmarks,
            "monte_carlo": mc_results,
            "robustness": {"mc": robustness, "rating": rating[0], "explanation": rating[1]},
            "latest_signal": explanation,
        }
        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        (out_dir / "report.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return True
    except Exception as e:
        logger.error("Failed to compute backtest results: %s", e)
        return False


def get_eth_data() -> pd.DataFrame | None:
    """Get ETH OHLCV data, auto-downloading if needed."""

    df = load_parquet("eth_ohlcv_1d")
    if df is None:
        ensure_data()
        df = load_parquet("eth_ohlcv_1d")
    return df


def get_results() -> pd.DataFrame | None:
    """Get backtest results, auto-downloading if needed."""

    df = load_parquet("latest_results")
    if df is None:
        ensure_data()
        df = load_parquet("latest_results")
    return df