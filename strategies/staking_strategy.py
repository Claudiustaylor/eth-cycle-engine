"""Staking wrapper strategy."""

from __future__ import annotations

import pandas as pd

from staking.model import StakingModel
from strategies.base import Strategy, TradeAction


class StakingStrategy(Strategy):
    """Wrap a price strategy and add staking bookkeeping hooks."""

    def __init__(self, strategy: Strategy, staking_model: StakingModel) -> None:
        self.strategy = strategy
        self.staking_model = staking_model

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        action = self.strategy.generate_signals(features_df, regime_series, current_idx, portfolio_state)
        row = features_df.iloc[current_idx]
        if action is None and portfolio_state.get("eth_units", 0) > portfolio_state.get("staked_eth", 0):
            unstaked = portfolio_state["eth_units"] - portfolio_state.get("staked_eth", 0)
            return TradeAction(row.name, "stake", unstaked, unstaked * row["close"], row["close"], "Auto-stake held ETH.", 50)
        return action

    def name(self) -> str:
        return f"{self.strategy.name()} + Staking"
