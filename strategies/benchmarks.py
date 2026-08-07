"""Benchmark strategies."""

from __future__ import annotations

from typing import Any

import pandas as pd

from strategies.base import Strategy, TradeAction


class BuyAndHold(Strategy):
    """Buy with all available cash on first day and hold."""

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        row = features_df.iloc[current_idx]
        if current_idx == 0 and portfolio_state["cash"] > 0:
            cash = portfolio_state["cash"]
            return TradeAction(row.name, "buy", cash / row["close"], cash, row["close"], "Initial buy-and-hold allocation.", 100)
        return None

    def name(self) -> str:
        return "Buy and Hold"


class BuyAndHoldStaked(BuyAndHold):
    """Buy-and-hold benchmark intended to be paired with staking."""

    def name(self) -> str:
        return "Buy and Hold Staked"


class DollarCostAveraging(Strategy):
    """Buy a fixed amount at regular intervals."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = (config or {}).get("dca", {})
        self.amount = float(cfg.get("amount", 250))
        self.frequency = cfg.get("frequency", "monthly")

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        row = features_df.iloc[current_idx]
        date = pd.Timestamp(row.name)
        do_buy = date.day == 1 if self.frequency == "monthly" else date.weekday() == 0
        amount = min(self.amount, portfolio_state["cash"])
        if do_buy and amount > 0:
            return TradeAction(row.name, "buy", amount / row["close"], amount, row["close"], "Scheduled DCA buy.", 50)
        return None

    def name(self) -> str:
        return "Dollar Cost Averaging"


class MovingAverage200(Strategy):
    """Buy above 200-day EMA and sell below it."""

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        row = features_df.iloc[current_idx]
        price = row["close"]
        if row.get("price_vs_ema_200", 0) > 0 and portfolio_state["cash"] > 0:
            cash = portfolio_state["cash"]
            return TradeAction(row.name, "buy", cash / price, cash, price, "Price above 200-day EMA.", 70)
        if row.get("price_vs_ema_200", 0) < 0 and portfolio_state["eth_units"] > 0:
            usd = portfolio_state["eth_units"] * price
            return TradeAction(row.name, "sell", portfolio_state["eth_units"], usd, price, "Price below 200-day EMA.", 30)
        return None

    def name(self) -> str:
        return "200-Day Moving Average"


class SimpleDrawdownBuying(Strategy):
    """Buy fixed amount when cycle drawdown exceeds a threshold."""

    def __init__(self, threshold: float = -0.20, amount: float = 1000) -> None:
        self.threshold = threshold
        self.amount = amount
        self.last_buy_idx = -999

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        row = features_df.iloc[current_idx]
        if row.get("drawdown_cycle", 0) <= self.threshold and current_idx - self.last_buy_idx >= 30:
            usd = min(self.amount, portfolio_state["cash"])
            if usd > 0:
                self.last_buy_idx = current_idx
                return TradeAction(row.name, "buy", usd / row["close"], usd, row["close"], "Drawdown threshold reached.", 65)
        return None

    def name(self) -> str:
        return "Simple Drawdown Buying"
