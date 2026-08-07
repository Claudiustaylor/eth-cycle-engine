"""Regime types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class Regime(Enum):
    """Explainable ETH market-cycle regimes."""

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


@dataclass(frozen=True)
class RegimeResult:
    """Regime result with date and explanation."""

    date: pd.Timestamp
    regime: Regime
    reason: str
