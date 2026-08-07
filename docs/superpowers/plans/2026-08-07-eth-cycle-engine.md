# ETH Cycle Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular ETH market-cycle research, backtesting, simulation, and dashboard system.

**Architecture:** The project is a flat Python package with independently importable modules for data ingestion, feature engineering, regime classification, signal scoring, strategies, risk, staking, backtesting, metrics, simulation, and Streamlit pages. Data ingestion uses real yfinance data and Parquet caching; paid data sources return unavailable fallbacks. Strategy and backtest paths are event-driven and pass only historical slices to avoid look-ahead.

**Tech Stack:** Python 3.11, pandas, numpy, scipy, yfinance, pyarrow, pyyaml, plotly, streamlit, pytest, ruff.

---

### Task 1: Scaffold and Config

**Files:**
- Create: `pyproject.toml`, `.gitignore`, package directories, `config/*.yaml`
- Test: import package modules

- [ ] Write failing smoke tests for imports and config loading.
- [ ] Add project metadata and dependencies.
- [ ] Add YAML configs for default, conservative, aggressive profiles.
- [ ] Run `pytest tests/test_smoke.py -v`.

### Task 2: Data and Features

**Files:**
- Create: `data/*.py`, `features/*.py`
- Test: `tests/test_data_ingestion.py`, `tests/test_features.py`

- [ ] Write deterministic tests for Parquet roundtrip, unavailable optional sources, and representative feature outputs.
- [ ] Implement schemas, storage, yfinance ingestion, and no-fabrication fallbacks.
- [ ] Implement all requested feature functions with rolling/current-bar-safe calculations.
- [ ] Run focused tests.

### Task 3: Regimes, Signals, Risk, Staking, Strategies

**Files:**
- Create: `regimes/*.py`, `signals/*.py`, `risk/*.py`, `staking/*.py`, `strategies/*.py`
- Test: corresponding unit tests

- [ ] Write tests for regimes, score bands, explanations, tranche sizing, staking rewards, and benchmark behavior.
- [ ] Implement explainable rule-based regimes, optional lazy ML classifier, signal scoring, anomaly handling, risk limits, staking model, and strategies.
- [ ] Run focused tests.

### Task 4: Backtesting, Metrics, Simulation, Dashboard, Example

**Files:**
- Create: `backtesting/*.py`, `metrics/*.py`, `simulation/*.py`, `dashboard/**/*.py`, `example_backtest.py`, `README.md`
- Test: corresponding unit tests

- [ ] Write tests for event-loop no-lookahead behavior, costs, metrics, Monte Carlo reproducibility, robustness, and walk-forward splits.
- [ ] Implement backtest engine, costs, tax model, walk-forward validation, metrics, Monte Carlo, scenarios, charts, dashboard pages, and runnable example.
- [ ] Run full verification: install, pytest, ruff, example script, Streamlit import check.
- [ ] Commit with the requested message and push if a remote exists.
