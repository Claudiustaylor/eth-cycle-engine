"""Portfolio risk limits."""

from __future__ import annotations

from typing import Any


class RiskLimits:
    """Check exposure and drawdown limits."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config.get("risk", {})

    def check_exposure(self, position_value: float, total_equity: float) -> bool:
        """Return True if ETH exposure is within limits."""

        return total_equity <= 0 or position_value / total_equity <= self.max_position_pct()

    def check_drawdown(self, current_drawdown: float) -> bool:
        """Return True if trading may continue under drawdown stop."""

        return abs(current_drawdown) <= float(self.config.get("max_drawdown_stop", 0.60))

    def max_position_pct(self) -> float:
        """Return max ETH exposure percentage."""

        return float(self.config.get("max_exposure", 0.95))

    def min_cash_reserve(self) -> float:
        """Return minimum cash reserve percentage."""

        return float(self.config.get("min_cash_reserve", 0.05))
