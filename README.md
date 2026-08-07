# ETH Cycle Engine

ETH Cycle Engine is a Python research system for explainable ETH market-cycle features, regimes, signals, strategy backtests, Monte Carlo simulations, and a Streamlit dashboard.

It uses real free yfinance data for ETH, BTC, and macro proxies. Optional paid on-chain and derivatives sources are explicit interfaces that return unavailable fallbacks when not configured. The project does not fabricate historical on-chain or derivatives values.

## Architecture

```text
yfinance/cache -> data -> features -> regimes -> signals -> strategies
                                      \              /
                                       backtesting -> metrics
                                       simulation  -> reports/dashboard
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

```bash
python example_backtest.py
```

This downloads ETH/BTC/macro data from yfinance, caches Parquet datasets under `data/parquet/`, computes features, classifies regimes, runs the signal strategy and benchmarks, runs Monte Carlo checks, and writes outputs under `output/`.

## Dashboard

```bash
streamlit run dashboard/app.py
```

If the dashboard has no cached results, run `python example_backtest.py` first.

## Modules

- `data/`: schemas, yfinance ingestion, unavailable fallbacks, Parquet storage.
- `features/`: trend, momentum, volatility, drawdown, volume, market structure, macro, optional derivatives and on-chain features.
- `regimes/`: explainable rule-based classifier plus optional lazy ML classifier.
- `signals/`: sub-scores, 0-100 combined score, and value-specific explanation text.
- `risk/`: tranche sizing, anomaly detection, exposure and drawdown limits.
- `staking/`: ETH-unit staking model with rewards and lockup support.
- `strategies/`: signal-driven, drawdown-buying, staking wrapper, and benchmarks.
- `backtesting/`: event-driven engine, transaction costs, tax model, walk-forward validation.
- `metrics/`: performance, risk, robustness, and overfitting checks.
- `simulation/`: bootstrap, regime-conditioned, Student-t, GARCH fallback, scenarios.
- `dashboard/`: Streamlit pages and Plotly components.

## Data Sources

| Source | Provider | Required? | Notes |
| --- | --- | --- | --- |
| ETH OHLCV | yfinance `ETH-USD` | Yes | Free, no API key |
| BTC OHLCV | yfinance `BTC-USD` | No | Used for relative strength |
| Macro | yfinance `^IRX`, `^GSPC`, `^IXIC`, `DX-Y.NYB` | No | CPI/Fed Funds are marked unavailable without FRED key |
| On-chain | Optional paid APIs | No | Returns `None` unless configured |
| Derivatives | Optional paid APIs | No | Returns `None` unless configured |
| Staking source | Config placeholder | No | Strategy staking model is independent from source data |

## Configuration

All strategy and system parameters live in YAML files under `config/`.

- `config/default.yaml`: balanced defaults.
- `config/conservative.yaml`: lower max exposure, higher cash reserve, smaller tranches.
- `config/aggressive.yaml`: higher max exposure, larger tranches, wider anomaly tolerance.

## No Look-Ahead Discipline

Features use trailing rolling windows, shifted prior highs where appropriate, and the backtest engine passes `features.iloc[:current_idx+1]` to strategies on each bar. Strategies receive only historical rows up to the current bar.

## Testing

```bash
pytest -v
ruff check .
```

Tests use synthetic deterministic data so they are fast and do not require network access.

## Limitations

This is a research/backtesting framework, not an execution system. yfinance data can revise or have outages. On-chain, derivatives, taxes, and staking economics are simplified unless real providers and jurisdiction-specific logic are added. Scenario and Monte Carlo outputs are distributions from historical returns, not forecasts.

## Disclaimer

This project is for educational and research use only. It is not financial advice, investment advice, tax advice, or a recommendation to buy or sell any asset.
