# ETH Cycle Engine — Full System Build

You are a senior quantitative developer building a production-quality ETH market-cycle backtesting and simulation system in Python.

Project root: `/Users/ct/eth-cycle-engine`

## CRITICAL RULES

1. **DO NOT fabricate data.** Every data source must be real or clearly marked as simulated/placeholder. Use `yfinance` for ETH, BTC, and macro data (free, no API key). For on-chain/derivatives data that requires paid APIs, implement the ingestion interface with a graceful "unavailable" fallback — never fabricate historical values.
2. **No look-ahead bias.** Every feature, signal, and backtest step must use only information available up to and including the current bar. Use `.shift()` or explicit rolling windows with `min_periods` to prevent future leakage.
3. **Modular architecture.** Each module must be independently importable and testable. Use dataclasses for config, Protocol/ABC for interfaces, and type hints everywhere.
4. **No external API keys required to run.** The system must work out of the box with free data (yfinance). Paid data sources are optional plugins that degrade gracefully.
5. **Reproducible.** Set random seeds everywhere randomness is used.
6. **Parquet storage.** Store all downloaded data as Parquet files under `data/parquet/`.
7. **Config-driven.** All strategy parameters live in YAML config files under `config/`.
8. **Every buy/sell signal must be explainable.** No black-box recommendations.

## FOLDER STRUCTURE

```
eth-cycle-engine/
├── data/
│   ├── __init__.py
│   ├── ingestion.py          # Data ingestion layer (yfinance + optional sources)
│   ├── schemas.py            # Dataclass schemas for OHLCV, on-chain, macro, etc.
│   ├── storage.py            # Parquet read/write utilities
│   └── parquet/              # Local Parquet data store (gitignored)
├── features/
│   ├── __init__.py
│   ├── trend.py              # EMA, slopes, crossovers
│   ├── momentum.py           # RSI, MACD, ROC, relative strength
│   ├── volatility.py         # ATR, realized vol, Bollinger, vol percentile
│   ├── drawdown.py           # Drawdown from ATH, cycle high, rolling DD
│   ├── volume.py             # Volume vs MA, acceleration, divergence
│   ├── market_structure.py   # HH/HL, LH/LL, breakouts, failed breakouts
│   ├── derivatives.py        # Funding rate, OI, leverage, liquidations
│   ├── onchain.py            # Exchange flows, MVRV, realized price, activity
│   ├── macro.py              # Risk-on/off, rates, DXY, equity trends
│   └── registry.py           # Feature registry — combines all features
├── regimes/
│   ├── __init__.py
│   ├── rule_based.py         # Explainable rule-based regime classification
│   ├── ml_based.py           # Optional HMM/clustering/RF/GBM regime models
│   └── types.py              # Regime enum + dataclass
├── signals/
│   ├── __init__.py
│   ├── scoring.py            # 0-100 confidence scoring engine
│   ├── sub_scores.py         # Valuation, trend, momentum, vol, deriv, onchain, macro, regime sub-scores
│   └── explainability.py     # Signal explanation generator
├── strategies/
│   ├── __init__.py
│   ├── base.py               # Abstract strategy interface
│   ├── drawdown_buying.py    # Drawdown-based accumulation
│   ├── signal_driven.py      # Signal-score-driven tranche accumulation
│   ├── benchmarks.py        # Buy-and-hold, DCA, 200-MA, simple drawdown
│   └── staking_strategy.py   # Combines price strategy + staking
├── risk/
│   ├── __init__.py
│   ├── position_sizing.py    # Tranche-based position sizing
│   ├── anomaly.py            # Anomaly detection + defensive mode
│   └── limits.py             # Risk limits, max exposure, drawdown caps
├── staking/
│   ├── __init__.py
│   └── model.py              # Staking yield model (independent of price)
├── simulation/
│   ├── __init__.py
│   ├── monte_carlo.py        # Monte Carlo with block bootstrap, regime-conditioned, Student-t
│   └── scenarios.py          # Scenario analysis (4yr, 5yr, 10yr)
├── backtesting/
│   ├── __init__.py
│   ├── engine.py             # Core backtesting engine (event-driven, no look-ahead)
│   ├── walk_forward.py       # Walk-forward validation
│   ├── costs.py              # Transaction costs (fees, spread, slippage)
│   └── tax.py                # Optional tax modeling
├── metrics/
│   ├── __init__.py
│   ├── performance.py        # CAGR, Sharpe, Sortino, Calmar, etc.
│   ├── risk.py               # VaR, CVaR, downside deviation
│   └── robustness.py         # Overfitting controls, parameter stability, sensitivity
├── dashboard/
│   ├── __init__.py
│   ├── app.py                # Streamlit dashboard entry point
│   ├── pages/
│   │   ├── overview.py       # Market overview
│   │   ├── regime.py         # Current regime
│   │   ├── signals.py        # Signal score + buy/sell indicators
│   │   ├── backtest.py       # Historical backtest
│   │   ├── drawdowns.py      # Drawdown analysis
│   │   ├── comparison.py     # Strategy comparison
│   │   ├── monte_carlo.py    # Monte Carlo
│   │   ├── staking.py        # Staking model
│   │   ├── scenarios.py      # Scenario simulator
│   │   ├── sensitivity.py   # Parameter sensitivity
│   │   └── trade_history.py  # Trade history
│   └── components/
│       └── charts.py         # Reusable chart components
├── tests/
│   ├── __init__.py
│   ├── test_data_ingestion.py
│   ├── test_features.py
│   ├── test_regimes.py
│   ├── test_signals.py
│   ├── test_position_sizing.py
│   ├── test_staking.py
│   ├── test_backtesting.py
│   ├── test_metrics.py
│   ├── test_monte_carlo.py
│   ├── test_overfitting.py
│   └── test_walk_forward.py
├── config/
│   ├── default.yaml           # Default strategy + system config
│   ├── conservative.yaml     # Conservative risk parameters
│   └── aggressive.yaml       # Aggressive parameters
├── data/parquet/              # Parquet data store (gitignored)
├── pyproject.toml
├── README.md
├── example_backtest.py       # Runnable example: download data, run backtest, print results
└── .gitignore
```

## IMPLEMENTATION SPECIFICATIONS

### Phase 1 — Project Setup & Data Layer

#### pyproject.toml
Create a pyproject.toml with:
- Project name: `eth-cycle-engine`
- Python >=3.11
- Dependencies: pandas, numpy, scipy, pyyaml, pyarrow, yfinance, plotly, streamlit, scikit-learn (optional ML), hmmlearn (optional), statsmodels, arch (for GARCH vol), pytest, pytest-cov, matplotlib, numba (optional speedup)
- Dev dependencies: ruff, mypy, pytest, pytest-cov
- `[tool.ruff]` config with line-length=100, target-version=py311
- `[tool.pytest.ini_options]` with testpaths=["tests"]
- Console script entry point: `eth-cycle = "dashboard.app:main"`

#### .gitignore
Standard Python gitignore + `data/parquet/` + `*.parquet` + `__pycache__/` + `.pytest_cache/` + `.mypy_cache/` + `.venv/` + `htmlcov/`

#### data/schemas.py
Define frozen dataclasses for:
- `OHLCVBar`: timestamp, open, high, low, close, volume
- `MacroData`: date, fed_funds_rate, cpi_yoy, dxy, treasury_10y, treasury_2y, sp500, nasdaq
- `OnChainData`: date, active_addresses, tx_volume, gas_fees, network_revenue, exchange_inflow, exchange_outflow, exchange_reserve, mvrv, realized_price, eth_supply
- `DerivativesData`: date, funding_rate, open_interest, liquidations_long, liquidations_short
- `StakingData`: date, staking_yield, total_staked, staking_ratio
- Each with proper types (pd.Timestamp, float, etc.)

#### data/storage.py
- `save_parquet(df, name, base_path="data/parquet/")` — saves with partitioning by year
- `load_parquet(name, base_path="data/parquet/")` — loads, returns DataFrame or None if not found
- `data_exists(name, base_path)` — bool check
- Use pyarrow engine

#### data/ingestion.py
Implement a `DataIngestion` class:
- `__init__(self, config: dict)` — reads enabled sources from config
- `fetch_eth_ohlcv(self, start, end, interval="1d")` — uses yfinance ticker "ETH-USD"
- `fetch_btc_ohlcv(self, start, end, interval="1d")` — uses yfinance ticker "BTC-USD"
- `fetch_macro(self, start, end)` — fetches ^IRX (T-bill), ^GSPC (S&P500), ^IXIC (Nasdaq), DX-Y.NYB (DXY). For CPI and Fed Funds Rate, use FRED API if key available, else mark as unavailable.
- `fetch_eth_btc_ratio(self, start, end)` — computed from ETH/BTC prices
- `fetch_onchain(self, start, end)` — returns None with warning if no API configured (NEVER fabricate)
- `fetch_derivatives(self, start, end)` — returns None with warning if no API configured
- `fetch_staking(self, start, end)` — returns None with warning if no API configured. Default staking yield from config (3%).
- `fetch_all(self, start, end)` — orchestrates all enabled sources, returns `DataSet` dataclass
- All methods cache to Parquet. If Parquet exists and is fresh (configurable max_age), load from cache.
- Every fetch method must have try/except, log warnings, and return None on failure.

### Phase 2 — Feature Engineering

#### features/trend.py
- `compute_emas(prices, periods=[20, 50, 100, 200])` — returns DataFrame with EMA columns
- `compute_ema_slope(ema, window=10)` — slope of EMA over window
- `price_vs_ma(prices, ema)` — price as ratio to EMA (price/ema - 1.0)
- `ma_crossovers(ema_short, ema_long)` — +1 bullish, -1 bearish, 0 neutral

#### features/momentum.py
- `compute_rsi(prices, period=14)` — Wilder's RSI
- `compute_macd(prices, fast=12, slow=26, signal=9)` — MACD line, signal line, histogram
- `rate_of_change(prices, period=14)` — ROC
- `momentum_percentile(prices, indicator, window=252)` — rolling percentile of indicator
- `relative_strength_vs_btc(eth_prices, btc_prices, window=90)` — RS ratio

#### features/volatility.py
- `compute_atr(highs, lows, closes, period=14)` — Average True Range
- `realized_volatility(returns, window=21)` — annualized realized vol
- `bollinger_band_width(closes, window=20, num_std=2)` — BB width as percentage of mean
- `volatility_percentile(realized_vol, window=252)` — rolling percentile
- `volatility_expansion(rv_short, rv_long)` — ratio of short-term to long-term vol

#### features/drawdown.py
- `drawdown_from_ath(prices)` — rolling all-time high drawdown
- `drawdown_from_cycle_high(prices, cycle_window=252)` — drawdown from rolling max over cycle window
- `drawdown_30d(prices)` — drawdown from 30-day high
- `drawdown_90d(prices)` — drawdown from 90-day high
- `max_trailing_drawdown(prices, window=252)` — max DD over trailing window

#### features/volume.py
- `volume_vs_ma(volume, window=20)` — volume / volume MA
- `volume_acceleration(volume, window=10)` — rate of change of volume
- `price_volume_divergence(prices, volume, window=20)` — price up + volume down = bearish divergence

#### features/market_structure.py
- `higher_highs_higher_lows(prices, window=20)` — boolean + streak count
- `lower_highs_lower_lows(prices, window=20)` — boolean + streak count
- `distance_from_local_high(prices, window=20)` — percentage below local high
- `distance_from_local_low(prices, window=20)` — percentage above local low
- `breakout_detection(prices, window=20)` — boolean breakout above local high
- `failed_breakout_detection(prices, window=20, lookback=5)` — broke out then fell back below

#### features/derivatives.py
- `funding_rate_percentile(funding, window=252)` — if data available, else None
- `open_interest_change(oi, window=7)` — if data available
- `leverage_expansion(oi, market_cap, window=14)` — if data available
- `liquidation_spikes(liquidations, window=7, threshold=3)` — z-score of liquidations
All derivative features return None series if input data is None.

#### features/onchain.py
- `exchange_inflow_percentile(inflow, window=252)`
- `exchange_outflow_percentile(outflow, window=252)`
- `mvrv_percentile(mvrv, window=252)`
- `realized_price_deviation(price, realized_price)`
- `network_activity_acceleration(active_addresses, window=14)`
All onchain features return None series if input data is None.

#### features/macro.py
- `risk_on_risk_off(sp500, dxy, vix_proxy=None, window=20)` — composite score: SP500 trending up + DXY trending down = risk-on
- `rate_direction(treasury_2y, window=20)` — slope of yields
- `dollar_strength_trend(dxy, window=20)` — DXY slope
- `equity_market_trend(sp500, window=50)` — above/below 50-day MA

#### features/registry.py
- `FeatureRegistry` class that:
  - Takes a `DataSet` and config
  - Computes all enabled features
  - Returns a single `pd.DataFrame` with all feature columns
  - Respects config flags to enable/disable feature groups
  - Logs which features were computed vs skipped (data unavailable)

### Phase 3 — Regime Detection

#### regimes/types.py
```python
from enum import Enum

class Regime(Enum):
    ACCUMULATION = "accumulation"
    EARLY_BULL = "early_bull"
    BULL_EXPANSION = "bull_expansion"
    LATE_BULL = "late_bull"
    BLOW_OFF = "blow_off"
    DISTRIBUTION = "distribution"
    EARLY_BEAR = "early_bear"
    CAPITULATION = "capitulation"
    RECOVERY = "recovery"
    SIDEWAYS = "sideways"
```

#### regimes/rule_based.py
Implement `RuleBasedRegimeClassifier`:
- `__init__(self, config)` — configurable thresholds
- `classify(self, features_df, current_idx) -> Regime` — uses only features available up to current_idx
- Classification logic (explainable, rule-based):
  - **ACCUMULATION**: Price 30-60% below cycle high, RSI 40-55, vol declining, 200-day EMA flat or declining but price above it occasionally, volume increasing on up days
  - **EARLY_BULL**: Price reclaimed 50-day EMA, 50-day EMA turning up, RSI 50-65, price 15-40% below cycle high, volume increasing
  - **BULL_EXPANSION**: Price above 50 and 200-day EMA, both EMAs rising, RSI 60-75, HH/HL pattern, 0-15% below cycle high
  - **LATE_BULL**: Price above 200-day EMA but 50-day EMA flattening, RSI >70 persistently, price near cycle high, volume diverging (price up, volume declining)
  - **BLOW_OFF**: RSI >80, parabolic price acceleration (price > 20% above 20-day EMA), extreme volume spike, funding extremely positive if available
  - **DISTRIBUTION**: Price 0-15% below cycle high, RSI 50-70 declining, 50-day EMA rolling over, volume high on down days, HH failing
  - **EARLY_BEAR**: Price below 50-day EMA, 50-day below 200-day EMA or approaching, RSI 35-50, LH/LL pattern, price 15-35% below cycle high
  - **CAPITULATION**: Price 40%+ below cycle high, RSI <30, extreme volume, vol at 90+ percentile, rapid decline
  - **RECOVERY**: Price 20-40% below cycle high but rising, RSI 45-60, 50-day EMA turning up from below, volume increasing
  - **SIDEWAYS**: None of the above dominate; price within 15% of 200-day EMA, RSI 45-55, low vol percentile
- `classify_series(self, features_df) -> pd.Series` — applies classification across full series (using only past data at each point)

#### regimes/ml_based.py
Implement `MLRegimeClassifier`:
- `__init__(self, method="hmm", config)` — supports "hmm", "kmeans", "logistic", "rf", "gbm"
- `fit(self, features_df, train_end_idx)` — fits only on data up to train_end_idx
- `predict(self, features_df, idx)` — predicts regime for idx using model fit on prior data
- `compare_with_rule_based(self, features_df, rule_based_labels)` — compares OOS performance
- IMPORTANT: All ML methods must be optional (lazy import). If sklearn/hmmlearn not available, log warning and return None.

### Phase 4 — Signal Engine

#### signals/scoring.py
Implement `SignalScoringEngine`:
- `__init__(self, config)` — loads scoring weights from config (all configurable)
- `compute_sub_scores(self, features_df, idx) -> dict[str, float]` — returns dict of sub-scores (0-100 each)
- `compute_combined_score(self, sub_scores) -> float` — weighted combination, 0-100
- `get_signal_band(self, score) -> tuple[str, str]` — returns (band_name, action)
  - 0-20: ("strong_sell", "extreme caution")
  - 21-40: ("reduce", "reduce exposure")
  - 41-59: ("neutral", "neutral")
  - 60-74: ("accumulate", "initial accumulation")
  - 75-89: ("strong_accumulate", "strong accumulation")
  - 90-100: ("extreme_accumulate", "extreme accumulation opportunity")

#### signals/sub_scores.py
Implement sub-score computation functions, each returning 0-100:
- `valuation_score(features, idx)`: Uses drawdown from cycle high, MVRV (if available), realized price deviation (if available). Deeper drawdowns + low MVRV = higher score.
- `trend_score(features, idx)`: Uses EMA positions, slopes, crossovers. Price above rising EMAs = high score.
- `momentum_score(features, idx)`: Uses RSI, MACD, ROC, momentum percentile. RSI in low deciles with positive MACD crossover = high score (contrarian + confirmation).
- `volatility_score(features, idx)`: Uses vol percentile, vol expansion/contraction. High vol + contracting = higher score (panic selling creating opportunity). Low vol = neutral.
- `derivatives_score(features, idx)`: Uses funding rate percentile, OI change, liquidation spikes. Negative funding + high liquidations = higher score (capitulation). Returns 50 (neutral) if no data.
- `onchain_score(features, idx)`: Uses exchange flows, MVRV percentile, network activity. Outflows elevated + low MVRV = high score. Returns 50 if no data.
- `macro_score(features, idx)`: Uses risk-on/off, rate direction, DXY trend, equity trend. Risk-on + falling rates + weak dollar = high score.
- `regime_score(features, idx, regime)`: Maps regime to score. Accumulation/Capitulation = high, Bull Expansion = moderate, Distribution/Blow-off = low.

#### signals/explainability.py
Implement `SignalExplainer`:
- `explain(self, sub_scores, combined_score, features_df, idx, regime, action) -> str`
- Returns a multi-line string in this format:
```
SIGNAL CONFIDENCE: 82/100
REGIME: accumulation

REASONS:
• ETH is 47% below cycle high (favorable for accumulation)
• RSI is in bottom historical decile (oversold)
• Funding is negative (traders bearish, contrarian bullish)
• Exchange outflows elevated (holders accumulating)
• Price reclaimed 200-day moving average (trend improving)
• Macro regime remains restrictive (caution)
• Realized volatility remains elevated (risk remains)

SUB-SCORES:
  Valuation:    85/100
  Trend:        62/100
  Momentum:     78/100
  Volatility:   55/100
  Derivatives:  70/100
  On-Chain:     68/100
  Macro:        35/100
  Regime:       90/100

RECOMMENDED ACTION: Deploy 20% of available dry powder.
```
- Only include reasons for sub-scores that have data (skip derivatives/onchain if unavailable)
- Each reason must reference a specific feature value

### Phase 5 — Position Sizing & Risk

#### risk/position_sizing.py
Implement `PositionSizer`:
- `__init__(self, config)` — loads tranche rules from config
- `size_by_score(self, score, available_cash, current_position_value, total_equity) -> float`
  - Returns USD amount to deploy (positive = buy, negative = sell)
  - Default tranches (configurable):
    - Score 60-69: deploy 10% of available cash
    - Score 70-79: deploy 15% of available cash
    - Score 80-89: deploy 25% of available cash
    - Score 90+: deploy 30% of available cash, subject to risk limits
  - For sell signals (score < 41):
    - Score 21-40: reduce 20% of position
    - Score 0-20: reduce 40% of position
- `size_drawdown_tranche(self, drawdown_pct, available_cash, method="fixed") -> float`
  - method="fixed": equal dollar amounts at each threshold
  - method="increasing": larger tranches as drawdown deepens
  - Drawdown thresholds: -10%, -20%, -30%, -40%, -50%, -60%, -70%, -80%
- `alternative_methods` property — supports Kelly criterion, volatility targeting (configurable)

#### risk/anomaly.py
Implement `AnomalyDetector`:
- `__init__(self, config)` — thresholds from config
- `detect(self, features_df, idx) -> AnomalyState`
  - Checks: z-score of returns > threshold, vol percentile > 95, volume spike > 5x MA, return outlier > 4 sigma, change-point detection (using statsmodels if available)
- `anomaly_action(self, anomaly_state) -> dict`
  - Returns: {reduce_position: float, suspend_entries: bool, widen_stops: float, defensive_mode: bool}
- During anomaly regimes: reduce position by up to 50%, suspend new entries, widen stops by 2x, enter defensive mode

#### risk/limits.py
Implement `RiskLimits`:
- `__init__(self, config)` — max exposure, max drawdown, etc.
- `check_exposure(self, position_value, total_equity) -> bool` — max % in ETH
- `check_drawdown(self, current_drawdown) -> bool` — stop trading if DD exceeds limit
- `max_position_pct(self) -> float` — max % of equity in ETH
- `min_cash_reserve(self) -> float` — minimum cash to keep

### Phase 6 — Staking

#### staking/model.py
Implement `StakingModel`:
- `__init__(self, config)` — annual yield, fees, compounding frequency, pct staked, lockup period, slashing risk
- `stake(self, eth_units, date)` — moves ETH into staking, records amount
- `unstake(self, eth_units, date)` — withdraws from staking (respecting lockup)
- `staking_reward(self, date) -> float` — daily staking reward in ETH
- `total_staked(self) -> float` — current staked ETH
- `staking_value_usd(self, eth_price) -> float` — USD value of staked ETH
- `rewards_earned(self) -> tuple[float, float]` — (total ETH rewards, total USD value at current price)
- `apply_compounding(self, date)` — compounds rewards into staked balance
- Default: 3% annual yield, 0% slashing, daily compounding, 100% of held ETH staked, no lockup
- Support 0%-6% yield range
- Track ETH units and USD value separately at all times

### Phase 7 — Strategies

#### strategies/base.py
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class TradeAction:
    date: pd.Timestamp
    action: str  # "buy", "sell", "stake", "unstake", "hold"
    eth_amount: float
    usd_amount: float
    price: float
    reason: str
    confidence: float

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, 
                         current_idx: int, portfolio_state: dict) -> Optional[TradeAction]:
        """Generate trading action for current bar. Uses only data up to current_idx."""
        pass
    
    @abstractmethod
    def name(self) -> str:
        pass
```

#### strategies/benchmarks.py
Implement 5 benchmark strategies:
1. `BuyAndHold` — buy 100% on first day, hold forever
2. `BuyAndHoldStaked` — buy 100% on first day, stake all, hold
3. `DollarCostAveraging` — buy fixed dollar amount at regular intervals (configurable: weekly, monthly)
4. `MovingAverage200` — buy when price > 200-day MA, sell when below
5. `SimpleDrawdownBuying` — buy fixed amount when drawdown exceeds threshold (default -20%)

#### strategies/signal_driven.py
Implement `SignalDrivenStrategy`:
- Uses `SignalScoringEngine` for confidence score
- Uses `PositionSizer` for tranche sizing
- Uses `AnomalyDetector` for defensive mode
- Uses `RiskLimits` for exposure checks
- `generate_signals()`:
  1. Compute combined score
  2. Check anomaly state → if anomaly, enter defensive mode
  3. If score >= 60 and not anomaly-suspended: deploy tranches per config
  4. If score <= 40: reduce position per config
  5. If staking enabled and holding ETH: auto-stake
  6. Generate `TradeAction` with explanation from `SignalExplainer`

#### strategies/drawdown_buying.py
Implement `DrawdownBuyingStrategy`:
- Monitors drawdown from cycle high
- At each drawdown threshold (-10% through -80%), deploys tranches
- Requires regime confirmation: only buy in ACCUMULATION, CAPITULATION, RECOVERY, or EARLY_BULL regimes
- Supports fixed-dollar and increasing-tranche methods
- Optionally requires trend confirmation (price > 50-day EMA) for shallower drawdowns

#### strategies/staking_strategy.py
Implement `StakingStrategy`:
- Wraps any price strategy and adds staking
- Manages staking lockup and rewards
- Tracks ETH units (staked + unstaked) and USD value separately

### Phase 8 — Backtesting

#### backtesting/costs.py
Implement `TransactionCosts`:
- `__init__(self, config)` — trading_fee_pct, spread_pct, slippage_pct, staking_fee_pct, withdrawal_fee
- `buy_cost(self, usd_amount) -> float` — returns total cost in USD
- `sell_cost(self, usd_amount) -> float` — returns net proceeds after costs
- `staking_fee(self, eth_amount, eth_price) -> float`

#### backtesting/engine.py
Implement `BacktestEngine`:
- `__init__(self, strategy, data, features, regime_series, config)` 
- `run(self, start_date, end_date, starting_capital=50000) -> BacktestResult`
  - Event-driven loop, bar by bar:
    1. Get current bar data (only up to current index)
    2. Update portfolio state (mark to market)
    3. Apply staking rewards if staking enabled
    4. Call strategy.generate_signals()
    5. If TradeAction: execute (apply costs, update positions)
    6. Record daily state: cash, ETH units (staked/unstaked), portfolio value, regime, signal score
  - STRICT: features_df.iloc[:current_idx+1] only. Never access future bars.
- `BacktestResult` dataclass with:
  - equity_curve: pd.Series (daily portfolio value)
  - eth_holdings: pd.Series
  - cash: pd.Series
  - staked_eth: pd.Series
  - trades: list[TradeAction]
  - regime_series: pd.Series
  - signal_scores: pd.Series
  - daily_returns: pd.Series
  - config used

#### backtesting/walk_forward.py
Implement `WalkForwardValidator`:
- `__init__(self, strategy, data, features, config)` 
- `run(self, train_years=3, test_years=1, method="expanding") -> list[WalkForwardResult]`
  - Expanding window: train [0:T], test [T:T+1], then train [0:T+1], test [T+1:T+2], etc.
  - Rolling window: train [T-3:T], test [T:T+1], then train [T-2:T+1], test [T+1:T+2], etc.
  - Each result: train_metrics, test_metrics, train_period, test_period
- `compare_windows(self, results) -> dict` — are results stable across windows?

#### backtesting/tax.py
Implement `TaxModel`:
- `__init__(self, config)` — mode ("none", "custom"), short_term_rate, long_term_rate, staking_income_rate, long_term_threshold_days
- `calculate_tax(self, trades, equity_curve) -> TaxResult`
  - Modes: no-tax, custom rates
  - Separates short-term vs long-term gains by holding period
  - Taxes staking income separately
  - Returns: TaxResult(total_tax, short_term_gains, long_term_gains, staking_income, after_tax_value, pre_tax_value)

### Phase 9 — Metrics

#### metrics/performance.py
Implement functions (all take returns/equity curve as input):
- `cagr(equity_curve)` — compound annual growth rate
- `total_return(equity_curve)` — total return %
- `annualized_volatility(returns)` — annualized stdev of daily returns
- `max_drawdown(equity_curve)` — maximum drawdown %
- `sharpe_ratio(returns, rf=0.02)` — annualized Sharpe
- `sortino_ratio(returns, rf=0.02)` — annualized Sortino (downside deviation only)
- `calmar_ratio(equity_curve)` — CAGR / max drawdown
- `win_rate(trades)` — % of profitable trades
- `profit_factor(trades)` — gross profit / gross loss
- `exposure_percentage(equity_curve, eth_holdings)` — % of time invested
- `average_holding_period(trades)` — average bars held
- `turnover(trades, equity_curve)` — annualized turnover
- `num_trades(trades)` — count
- `worst_year(returns)` — worst calendar year return
- `best_year(returns)` — best calendar year return
- `recovery_time(equity_curve)` — time to recover from max drawdown
- `final_portfolio_value(equity_curve)` — last value
- `eth_units_accumulated(trades)` — net ETH held
- `cash_balance(cash_series)` — final cash
- `staking_rewards_earned(staking_model)` — total rewards
- `fees_paid(cost_model, trades)` — total fees
- `generate_report(equity_curve, returns, trades, ...) -> dict` — returns all metrics in a dict

#### metrics/risk.py
- `value_at_risk(returns, confidence=0.95)` — historical VaR
- `conditional_var(returns, confidence=0.95)` — expected shortfall
- `downside_deviation(returns, mar=0)` — downside deviation
- `ulcer_index(equity_curve)` — Ulcer index

#### metrics/robustness.py
Implement overfitting controls:
- `parameter_stability(strategy, data, param_name, param_range, metric_fn) -> dict`
  - Runs strategy across a range of parameter values, reports metric for each
  - Stable strategy: metric doesn't collapse with small param changes
- `sensitivity_analysis(strategy, data, param_perturbation=0.1) -> dict`
  - Perturbs all parameters by ±10%, reports metric distribution
- `feature_ablation(features_df, signal_engine, metric_fn) -> dict`
  - Removes one feature group at a time, measures impact on signal quality
- `monte_carlo_reshuffling(returns, n_permutations=1000) -> dict`
  - Shuffles return order, recomputes Sharpe, reports p-value of actual Sharpe vs shuffled
- `multiple_testing_correction(p_values, method="bonferroni") -> list`
  - Adjusts p-values for multiple comparisons
- `robustness_rating(stability, sensitivity, ablation, mc_pvalue) -> tuple[str, str]`
  - Returns (rating, explanation) where rating is "strong", "moderate", "weak", "likely_overfit"

### Phase 10 — Monte Carlo & Scenarios

#### simulation/monte_carlo.py
Implement `MonteCarloEngine`:
- `__init__(self, config)` — n_simulations=10000, seed=42
- Methods (all return dict with percentiles 10/25/50/75/90, prob_loss, prob_target, prob_drawdown_50):
  - `bootstrap_resample(returns, horizon=252, n_sims=10000)` — iid bootstrap
  - `block_bootstrap(returns, block_size=21, horizon=252, n_sims=10000)` — block bootstrap preserving autocorrelation
  - `regime_conditioned(returns, regimes, horizon=252, n_sims=10000)` — samples from regime-specific return distributions
  - `student_t_simulation(returns, horizon=252, n_sims=10000)` — fit Student-t, simulate
  - `garch_simulation(returns, horizon=252, n_sims=10000)` — fit GARCH(1,1), simulate (using arch package)
- `report(simulation_results) -> dict` — percentiles, prob of loss, prob of target, prob of 50%+ DD

#### simulation/scenarios.py
Implement `ScenarioAnalyzer`:
- `__init__(self, config)`
- `run_scenarios(self, strategy, data, periods) -> dict`
  - periods: {"4yr": 4, "5yr": 5, "10yr": 10}
  - For each period, run strategy on: severe bear, bear/base, historical-like, moderate bull, strong bull, extreme repeat
  - Scenario construction: resample from historical periods matching scenario type
  - Severe bear: sample from ETH bear market periods (2018, 2022)
  - Strong bull: sample from ETH bull periods (2017, 2020-21)
  - Extreme: replay actual 2017-2018 cycle returns
  - Do NOT present extreme as expected. Label clearly.
- `format_results(results) -> pd.DataFrame`

### Phase 11 — Dashboard

#### dashboard/app.py
Streamlit main app:
```python
import streamlit as st
import sys
from pathlib import Path

# Page definitions
pages = [
    st.Page("dashboard/pages/overview.py", title="Market Overview", icon="📊"),
    st.Page("dashboard/pages/regime.py", title="Current Regime", icon="🎯"),
    st.Page("dashboard/pages/signals.py", title="Signal Score", icon="📡"),
    st.Page("dashboard/pages/backtest.py", title="Historical Backtest", icon="📜"),
    st.Page("dashboard/pages/drawdowns.py", title="Drawdown Analysis", icon="📉"),
    st.Page("dashboard/pages/comparison.py", title="Strategy Comparison", icon="⚖️"),
    st.Page("dashboard/pages/monte_carlo.py", title="Monte Carlo", icon="🎲"),
    st.Page("dashboard/pages/staking.py", title="Staking Model", icon="⛏️"),
    st.Page("dashboard/pages/scenarios.py", title="Scenario Simulator", icon="🔮"),
    st.Page("dashboard/pages/sensitivity.py", title="Parameter Sensitivity", icon="🔧"),
    st.Page("dashboard/pages/trade_history.py", title="Trade History", icon="📋"),
]

pg = st.navigation(pages)
pg.run()
```
Each page should be functional with real charts (plotly), using cached data loading. If data hasn't been downloaded, show instructions to run `example_backtest.py` first.

#### dashboard/components/charts.py
Reusable chart functions:
- `price_chart_with_signals(prices, buy_signals, sell_signals, regimes)` — candlestick + markers + regime shading
- `equity_curve_chart(equity, benchmark_equity)` — strategy vs buy-and-hold
- `drawdown_chart(equity)` — underwater plot
- `exposure_chart(cash, eth_value)` — cash vs ETH over time
- `signal_confidence_chart(scores)` — 0-100 over time with bands
- `rolling_sharpe_chart(returns, window=252)` — rolling Sharpe
- `rolling_volatility_chart(returns, window=21)` — rolling annualized vol
- All using plotly for interactivity

### Phase 12 — Configuration

#### config/default.yaml
```yaml
system:
  starting_capital: 50000
  data_start: "2017-11-01"  # ETH spot market data availability
  data_end: "2024-12-31"
  random_seed: 42

data:
  sources:
    eth_ohlcv: { enabled: true, provider: "yfinance" }
    btc_ohlcv: { enabled: true, provider: "yfinance" }
    macro: { enabled: true, provider: "yfinance" }
    onchain: { enabled: false, provider: "none" }  # requires paid API
    derivatives: { enabled: false, provider: "none" }
    staking: { enabled: false, provider: "config", default_yield: 0.03 }
  cache:
    max_age_hours: 24
    path: "data/parquet/"

features:
  trend: { enabled: true, ema_periods: [20, 50, 100, 200] }
  momentum: { enabled: true, rsi_period: 14, macd: [12, 26, 9] }
  volatility: { enabled: true, atr_period: 14, rv_window: 21 }
  drawdown: { enabled: true, cycle_window: 252 }
  volume: { enabled: true, volume_ma: 20 }
  market_structure: { enabled: true, structure_window: 20 }
  derivatives: { enabled: false }
  onchain: { enabled: false }
  macro: { enabled: true }

regimes:
  method: "rule_based"
  ml_method: null  # "hmm", "kmeans", "rf", "gbm" if ML desired

signals:
  weights:
    valuation: 0.20
    trend: 0.15
    momentum: 0.15
    volatility: 0.10
    derivatives: 0.10
    onchain: 0.10
    macro: 0.10
    regime: 0.10
  bands:
    strong_sell: [0, 20]
    reduce: [21, 40]
    neutral: [41, 59]
    accumulate: [60, 74]
    strong_accumulate: [75, 89]
    extreme_accumulate: [90, 100]

position_sizing:
  method: "tranche"  # "tranche", "kelly", "vol_target"
  tranches:
    buy:
      60: 0.10  # score: pct of available cash
      70: 0.15
      80: 0.25
      90: 0.30
    sell:
      40: 0.20  # score: pct of position to sell
      20: 0.40
  drawdown_buying:
    method: "increasing"  # "fixed" or "increasing"
    thresholds: [-0.10, -0.20, -0.30, -0.40, -0.50, -0.60, -0.70, -0.80]
    require_regime_confirmation: true
    require_trend_confirmation: false

risk:
  max_exposure: 0.95  # max % of equity in ETH
  min_cash_reserve: 0.05
  max_drawdown_stop: 0.60  # stop trading if DD exceeds 60%
  anomaly:
    return_zscore_threshold: 4.0
    vol_percentile_threshold: 95
    volume_spike_multiple: 5.0
    defensive_reduction: 0.50

staking:
  enabled: true
  annual_yield: 0.03
  validator_fee: 0.0
  compounding_frequency: "daily"
  pct_staked: 1.0  # 100% of held ETH
  lockup_days: 0  # no lockup in default
  slashing_risk: 0.0

transaction_costs:
  trading_fee_pct: 0.001  # 0.1% per trade
  spread_pct: 0.0005  # 0.05%
  slippage_pct: 0.001  # 0.1%
  staking_fee_pct: 0.0
  withdrawal_fee: 0.0

tax:
  enabled: false
  mode: "none"  # "none" or "custom"
  short_term_rate: 0.37
  long_term_rate: 0.20
  staking_income_rate: 0.37
  long_term_threshold_days: 365

backtest:
  starting_capital: 50000
  walk_forward:
    train_years: 3
    test_years: 1
    method: "expanding"  # "expanding" or "rolling"

monte_carlo:
  n_simulations: 10000
  horizon_days: 252
  methods: ["block_bootstrap", "regime_conditioned", "student_t"]
  seed: 42

scenarios:
  periods: { "4yr": 4, "5yr": 5, "10yr": 10 }
  cases: ["severe_bear", "bear_base", "historical_cycle", "moderate_bull", "strong_bull", "extreme_repeat"]

overfitting:
  param_perturbation: 0.10
  mc_permutations: 1000
  significance_level: 0.05
```

#### config/conservative.yaml
Same structure as default.yaml but:
- Lower max exposure (0.70)
- Higher min cash reserve (0.15)
- Lower max drawdown stop (0.40)
- Smaller position tranches
- More conservative anomaly thresholds
- Higher staking_pct (if staking, stake 100%)

#### config/aggressive.yaml
Same structure but:
- Higher max exposure (0.98)
- Lower min cash reserve (0.02)
- Higher max drawdown stop (0.75)
- Larger position tranches
- Less conservative anomaly thresholds

### Phase 13 — Tests

Write unit tests for:
- test_data_ingestion.py: Test Parquet caching, data availability checks, graceful None on failed fetch
- test_features.py: Test each feature computation on synthetic data, verify no look-ahead (compare rolling vs shifted), test edge cases (insufficient data, NaN handling)
- test_regimes.py: Test rule-based classifier on synthetic regimes, verify each regime maps correctly, test OOS property (classify at idx only uses data up to idx)
- test_signals.py: Test scoring ranges (0-100), test band boundaries, test sub-score computation, test explainability output format
- test_position_sizing.py: Test tranche sizing at each score band, test drawdown buying thresholds, test risk limits
- test_staking.py: Test compounding, test lockup, test reward calculation, test USD tracking
- test_backtesting.py: Test no look-ahead (compare with/without future data), test cost application, test benchmark strategies, test equity curve correctness
- test_metrics.py: Test CAGR, Sharpe, max DD, VaR, CVaR on known data
- test_monte_carlo.py: Test bootstrap, block bootstrap, regime-conditioned, verify percentile outputs, test reproducibility (same seed = same result)
- test_overfitting.py: Test parameter stability, sensitivity analysis, MC reshuffling p-value
- test_walk_forward.py: Test expanding and rolling windows, verify train/test separation, test metric stability

All tests must pass. Use synthetic data (not yfinance) for unit tests to keep them fast and deterministic. Create a `tests/conftest.py` with fixtures for synthetic OHLCV data, features, etc.

### Phase 14 — Example Backtest

#### example_backtest.py
A fully runnable script that:
1. Creates a virtual environment and installs deps (or assumes deps installed)
2. Downloads ETH data from yfinance (2017-11-01 to 2024-12-31)
3. Downloads BTC data
4. Downloads macro data (S&P500, Nasdaq, DXY, T-bill)
5. Computes all features
6. Runs regime detection
7. Runs the signal-driven strategy
8. Runs all 5 benchmark strategies
9. Computes all performance metrics
10. Runs walk-forward validation
10. Runs Monte Carlo (block bootstrap, 1000 sims for speed)
11. Runs overfitting checks (param stability, MC reshuffling)
12. Prints a comprehensive report to stdout including:
    - Strategy vs benchmarks comparison table
    - All performance metrics
    - Walk-forward results
    - MC percentiles
    - Robustness rating
    - Signal explanation for the most recent bar
    - Staking breakdown
13. Saves all results to `output/` directory as JSON + Parquet
14. Prints: "Dashboard: run `streamlit run dashboard/app.py` to explore interactively"

The script must be runnable as: `python example_backtest.py`

### Phase 15 — README

#### README.md
Comprehensive README with:
- Project overview
- Architecture diagram (ASCII)
- Module descriptions
- Installation instructions (venv, pip install -e ".[dev]")
- Quick start: `python example_backtest.py`
- Dashboard: `streamlit run dashboard/app.py`
- Configuration guide (config/default.yaml explanation)
- Data sources table (what's available, what needs API keys)
- Testing: `pytest -v`
- Limitations section (honest about what this system can and cannot do)
- Disclaimer: not financial advice, educational/research tool only

## DESIGN PRINCIPLES (MUST FOLLOW)

1. **No look-ahead bias.** This is the #1 rule. Every feature must use `.shift(1)` or rolling windows that don't include the current bar's future. The backtest engine must pass `features_df.iloc[:current_idx+1]` to strategies.
2. **No fabricated data.** If on-chain, derivatives, or staking data is unavailable, return None and log a warning. The system must function with just OHLCV + macro data.
3. **Graceful degradation.** Every optional data source must be disableable via config without breaking any other module.
4. **Explainability.** Every signal must explain itself with specific feature values.
5. **Config-driven.** No hardcoded thresholds in code. Everything in YAML.
6. **Type hints everywhere.** Use `from __future__ import annotations` where helpful.
7. **Docstrings.** Every public class and function has a docstring.
8. **Error handling.** try/except around all external data calls. Log warnings, don't crash.
9. **Reproducibility.** All random operations use a seed from config.
10. **Parquet storage.** All downloaded data cached locally as Parquet.
11. **Modular imports.** ML libraries (sklearn, hmmlearn) are lazy-imported inside functions, not at module level.
12. **Separate ETH units and USD value.** Staking tracks ETH units independently from price.

## END REQUIREMENTS

1. `pip install -e ".[dev]"` succeeds with zero errors.
2. `pytest -v` passes all tests.
3. `python example_backtest.py` runs end-to-end and prints results (requires network for yfinance download).
4. `streamlit run dashboard/app.py` launches without import errors.
5. `ruff check .` passes with zero errors.
6. README.md is comprehensive.
7. Commit with message: `feat: full ETH cycle engine — data, features, regimes, signals, strategies, backtesting, MC, dashboard, tests`
8. Push to origin (if remote exists, else just commit).

Do NOT downgrade any dependencies. Use latest stable versions. Return a summary of all files created and any deviations from this spec.