"""Signal-score-driven tranche strategy."""

from __future__ import annotations

from typing import Any

import pandas as pd

from regimes.types import Regime
from risk.anomaly import AnomalyDetector
from risk.limits import RiskLimits
from risk.position_sizing import PositionSizer
from signals.explainability import SignalExplainer
from signals.scoring import SignalScoringEngine
from strategies.base import Strategy, TradeAction


class SignalDrivenStrategy(Strategy):
    """Use signal confidence, risk limits, and anomaly checks to trade."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.engine = SignalScoringEngine(config)
        self.sizer = PositionSizer(config)
        self.anomaly = AnomalyDetector(config)
        self.limits = RiskLimits(config)
        self.explainer = SignalExplainer()
        self.last_score = 50.0

    def generate_signals(self, features_df: pd.DataFrame, regime_series: pd.Series, current_idx: int, portfolio_state: dict) -> TradeAction | None:
        row = features_df.iloc[current_idx]
        regime_raw = regime_series.iloc[current_idx] if len(regime_series) > current_idx else "sideways"
        regime = Regime(regime_raw) if regime_raw in Regime._value2member_map_ else Regime.SIDEWAYS
        sub = self.engine.compute_sub_scores(features_df, current_idx, regime)
        score = self.engine.compute_combined_score(sub)
        self.last_score = score
        _, action_text = self.engine.get_signal_band(score)
        anomaly_state = self.anomaly.detect(features_df, current_idx)
        defensive = self.anomaly.anomaly_action(anomaly_state)
        price = float(row["close"])
        position_value = portfolio_state["eth_units"] * price
        usd = self.sizer.size_by_score(score, portfolio_state["cash"], position_value, portfolio_state["equity"])
        if defensive["suspend_entries"] and usd > 0:
            usd = 0.0
        if usd > 0:
            max_eth_value = portfolio_state["equity"] * self.limits.max_position_pct()
            usd = min(usd, max(0.0, max_eth_value - position_value))
            cash_reserve = portfolio_state["equity"] * self.limits.min_cash_reserve()
            usd = min(usd, max(0.0, portfolio_state["cash"] - cash_reserve))
        if abs(usd) < 1e-9:
            return None
        trade_action = "buy" if usd > 0 else "sell"
        reason = self.explainer.explain(sub, score, features_df, current_idx, regime, action_text)
        return TradeAction(row.name, trade_action, abs(usd) / price, abs(usd), price, reason, score)

    def name(self) -> str:
        return "Signal Driven"
