"""ETH staking model with unit-based accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class StakingPosition:
    """Staked ETH position lot."""

    eth_units: float
    date: pd.Timestamp


class StakingModel:
    """Track staked ETH units, rewards, lockups, and USD value separately."""

    def __init__(self, config: dict[str, Any]) -> None:
        cfg = config.get("staking", config)
        self.annual_yield = min(0.06, max(0.0, float(cfg.get("annual_yield", 0.03))))
        self.validator_fee = float(cfg.get("validator_fee", 0.0))
        self.compounding_frequency = cfg.get("compounding_frequency", "daily")
        self.pct_staked = float(cfg.get("pct_staked", 1.0))
        self.lockup_days = int(cfg.get("lockup_days", 0))
        self.slashing_risk = float(cfg.get("slashing_risk", 0.0))
        self.positions: list[StakingPosition] = []
        self.pending_rewards = 0.0
        self.total_rewards = 0.0
        self.last_reward_date: pd.Timestamp | None = None
        self.last_price = 0.0

    def stake(self, eth_units: float, date: pd.Timestamp) -> None:
        """Move ETH units into staking."""

        if eth_units > 0:
            self.positions.append(StakingPosition(float(eth_units), pd.Timestamp(date)))

    def unstake(self, eth_units: float, date: pd.Timestamp) -> float:
        """Withdraw eligible staked ETH units respecting lockup."""

        remaining = eth_units
        withdrawn = 0.0
        for pos in list(self.positions):
            if (pd.Timestamp(date) - pos.date).days < self.lockup_days:
                continue
            take = min(pos.eth_units, remaining)
            pos.eth_units -= take
            withdrawn += take
            remaining -= take
            if pos.eth_units <= 1e-12:
                self.positions.remove(pos)
            if remaining <= 1e-12:
                break
        return withdrawn

    def staking_reward(self, date: pd.Timestamp) -> float:
        """Accrue and return daily staking reward in ETH."""

        date = pd.Timestamp(date)
        days = 1 if self.last_reward_date is None else max((date - self.last_reward_date).days, 0)
        daily_rate = (self.annual_yield * (1 - self.validator_fee) - self.slashing_risk) / 365
        reward = self.total_staked() * daily_rate * days
        self.pending_rewards += reward
        self.total_rewards += reward
        self.last_reward_date = date
        return reward

    def total_staked(self) -> float:
        """Return current staked ETH units."""

        return float(sum(p.eth_units for p in self.positions))

    def staking_value_usd(self, eth_price: float) -> float:
        """Return USD value of staked ETH at current price."""

        self.last_price = float(eth_price)
        return self.total_staked() * self.last_price

    def rewards_earned(self) -> tuple[float, float]:
        """Return total rewards in ETH and USD at last known price."""

        return self.total_rewards, self.total_rewards * self.last_price

    def apply_compounding(self, date: pd.Timestamp) -> None:
        """Compound pending rewards into staked balance."""

        if self.pending_rewards > 0 and self.compounding_frequency == "daily":
            self.stake(self.pending_rewards, pd.Timestamp(date))
            self.pending_rewards = 0.0
