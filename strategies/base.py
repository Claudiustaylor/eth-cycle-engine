"""Strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class TradeAction:
    """Strategy trade action."""

    date: pd.Timestamp
    action: str
    eth_amount: float
    usd_amount: float
    price: float
    reason: str
    confidence: float


class Strategy(ABC):
    """Abstract strategy interface."""

    @abstractmethod
    def generate_signals(
        self,
        features_df: pd.DataFrame,
        regime_series: pd.Series,
        current_idx: int,
        portfolio_state: dict,
    ) -> TradeAction | None:
        """Generate current-bar action from historical feature slice."""

    @abstractmethod
    def name(self) -> str:
        """Return strategy name."""
