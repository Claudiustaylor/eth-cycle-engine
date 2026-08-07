"""Position sizing utilities."""

from __future__ import annotations

from typing import Any


class PositionSizer:
    """Tranche-based position sizing."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.cfg = config.get("position_sizing", {})

    def size_by_score(
        self, score: float, available_cash: float, current_position_value: float, total_equity: float
    ) -> float:
        """Return USD trade size: positive buy, negative sell."""

        _ = total_equity
        buy = self.cfg.get("tranches", {}).get("buy", {60: 0.10, 70: 0.15, 80: 0.25, 90: 0.30})
        sell = self.cfg.get("tranches", {}).get("sell", {40: 0.20, 20: 0.40})
        if score >= 90:
            return available_cash * float(buy.get(90, 0.30))
        if score >= 80:
            return available_cash * float(buy.get(80, 0.25))
        if score >= 70:
            return available_cash * float(buy.get(70, 0.15))
        if score >= 60:
            return available_cash * float(buy.get(60, 0.10))
        if score <= 20:
            return -current_position_value * float(sell.get(20, 0.40))
        if score <= 40:
            return -current_position_value * float(sell.get(40, 0.20))
        return 0.0

    def size_drawdown_tranche(
        self, drawdown_pct: float, available_cash: float, method: str = "fixed"
    ) -> float:
        """Return tranche size for drawdown threshold."""

        thresholds = self.cfg.get("drawdown_buying", {}).get(
            "thresholds", [-0.10, -0.20, -0.30, -0.40, -0.50, -0.60, -0.70, -0.80]
        )
        hits = [t for t in thresholds if drawdown_pct <= t]
        if not hits:
            return 0.0
        if method == "increasing":
            return available_cash * min(0.05 * len(hits), 0.35)
        return available_cash / max(len(thresholds), 1)

    @property
    def alternative_methods(self) -> list[str]:
        """Supported alternative sizing methods."""

        return ["kelly", "vol_target"]
