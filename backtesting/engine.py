"""Event-driven backtesting engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from backtesting.costs import TransactionCosts
from staking.model import StakingModel
from strategies.base import Strategy, TradeAction


@dataclass
class BacktestResult:
    """Backtest output data."""

    equity_curve: pd.Series
    eth_holdings: pd.Series
    cash: pd.Series
    staked_eth: pd.Series
    trades: list[TradeAction]
    regime_series: pd.Series
    signal_scores: pd.Series
    daily_returns: pd.Series
    config: dict[str, Any]


class BacktestEngine:
    """Run a strategy bar by bar without exposing future rows to strategies."""

    def __init__(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        features: pd.DataFrame,
        regime_series: pd.Series,
        config: dict[str, Any],
    ) -> None:
        self.strategy = strategy
        self.data = data
        self.features = features
        self.regime_series = regime_series
        self.config = config
        self.costs = TransactionCosts(config)
        self.staking = StakingModel(config) if config.get("staking", {}).get("enabled", False) else None

    def run(self, start_date: str | pd.Timestamp, end_date: str | pd.Timestamp, starting_capital: float = 50000) -> BacktestResult:
        """Run event-driven backtest over an inclusive date range."""

        features = self.features.loc[pd.Timestamp(start_date) : pd.Timestamp(end_date)].copy()
        cash = float(starting_capital)
        eth_units = 0.0
        trades: list[TradeAction] = []
        rows: list[dict[str, float]] = []
        scores: list[float] = []
        for i, (date, row) in enumerate(features.iterrows()):
            price = float(row["close"])
            if self.staking is not None:
                self.staking.staking_reward(date)
                self.staking.apply_compounding(date)
            staked = self.staking.total_staked() if self.staking else 0.0
            equity = cash + eth_units * price
            state = {"cash": cash, "eth_units": eth_units, "staked_eth": staked, "equity": equity}
            hist_features = features.iloc[: i + 1]
            hist_regimes = self.regime_series.reindex(features.index).iloc[: i + 1]
            action = self.strategy.generate_signals(hist_features, hist_regimes, i, state)
            if action is not None:
                if action.action == "buy" and cash > 0:
                    usd = min(action.usd_amount, cash)
                    fee = self.costs.buy_cost(usd)
                    net = max(0.0, usd - fee)
                    eth_units += net / price
                    cash -= usd
                    trades.append(action)
                elif action.action == "sell" and eth_units > 0:
                    units = min(action.eth_amount, eth_units)
                    gross = units * price
                    cash += self.costs.sell_cost(gross)
                    eth_units -= units
                    trades.append(action)
                elif action.action == "stake" and self.staking is not None:
                    units = min(action.eth_amount, max(0.0, eth_units - staked))
                    self.costs.staking_fee(units, price)
                    self.staking.stake(units, date)
                    trades.append(action)
            staked = self.staking.total_staked() if self.staking else 0.0
            equity = cash + eth_units * price
            rows.append({"cash": cash, "eth_units": eth_units, "staked_eth": staked, "equity": equity})
            scores.append(float(getattr(self.strategy, "last_score", 50.0)))
        states = pd.DataFrame(rows, index=features.index)
        equity_curve = states["equity"]
        return BacktestResult(
            equity_curve=equity_curve,
            eth_holdings=states["eth_units"],
            cash=states["cash"],
            staked_eth=states["staked_eth"],
            trades=trades,
            regime_series=self.regime_series.reindex(features.index),
            signal_scores=pd.Series(scores, index=features.index, name="signal_score"),
            daily_returns=equity_curve.pct_change().fillna(0),
            config=self.config,
        )
