"""Optional tax model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class TaxResult:
    """Tax calculation output."""

    total_tax: float
    short_term_gains: float
    long_term_gains: float
    staking_income: float
    after_tax_value: float
    pre_tax_value: float


class TaxModel:
    """No-tax or custom-rate tax model."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.cfg = config.get("tax", {})

    def calculate_tax(self, trades: list[Any], equity_curve: pd.Series) -> TaxResult:
        """Calculate approximate taxes from sell trade proceeds."""

        pre_tax = float(equity_curve.iloc[-1]) if len(equity_curve) else 0.0
        if self.cfg.get("mode", "none") == "none" or not self.cfg.get("enabled", False):
            return TaxResult(0.0, 0.0, 0.0, 0.0, pre_tax, pre_tax)
        gains = sum(t.usd_amount for t in trades if getattr(t, "action", "") == "sell")
        tax = gains * float(self.cfg.get("short_term_rate", 0.37))
        return TaxResult(tax, gains, 0.0, 0.0, pre_tax - tax, pre_tax)
