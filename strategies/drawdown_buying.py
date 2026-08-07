"""Drawdown-based accumulation strategy."""

from __future__ import annotations

from typing import Any

import pandas as pd

from regimes.types import Regime
from risk.position_sizing import PositionSizer
from strategies.base import Strategy, TradeAction


class DrawdownBuyingStrategy(Strategy):
    """Deploy tranches at drawdown thresholds with optional regime confirmation."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.sizer = PositionSizer(config)
        self.hit_thresholds: set[float] = set()
        self.allowed = {
            Regime.ACCUMULATION.value,
            Regime.CAPITULATION.value,
            Regime.RECOVERY.value,
            Regime.EARLY_BULL.value,
        }

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        row = features_df.iloc[current_idx]
        dd = float(row.get("drawdown_cycle", 0) or 0)
        cfg = self.config.get("position_sizing", {}).get("drawdown_buying", {})
        if cfg.get("require_regime_confirmation", True) and regime_series.iloc[current_idx] not in self.allowed:
            return None
        if cfg.get("require_trend_confirmation", False) and row.get("price_vs_ema_50", 0) <= 0 and dd > -0.30:
            return None
        thresholds = cfg.get("thresholds", [-0.10, -0.20, -0.30, -0.40, -0.50, -0.60, -0.70, -0.80])
        fresh = [t for t in thresholds if dd <= t and t not in self.hit_thresholds]
        if not fresh:
            return None
        threshold = min(fresh)
        self.hit_thresholds.add(threshold)
        usd = self.sizer.size_drawdown_tranche(dd, portfolio_state["cash"], cfg.get("method", "fixed"))
        if usd <= 0:
            return None
        return TradeAction(row.name, "buy", usd / row["close"], usd, row["close"], f"Cycle drawdown {dd:.1%} crossed {threshold:.0%}.", 70)

    def name(self) -> str:
        return "Drawdown Buying"
