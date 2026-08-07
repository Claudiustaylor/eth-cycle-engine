"""Explainable rule-based regime classifier."""

from __future__ import annotations

from typing import Any

import pandas as pd

from regimes.types import Regime


class RuleBasedRegimeClassifier:
    """Classify market regimes from trailing feature values."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def classify(self, features_df: pd.DataFrame, current_idx: int) -> Regime:
        """Classify a single index using only rows through current_idx."""

        hist = features_df.iloc[: current_idx + 1]
        row = hist.iloc[-1]
        dd = float(row.get("drawdown_cycle", 0) or 0)
        rsi = float(row.get("rsi", 50) if pd.notna(row.get("rsi", 50)) else 50)
        pv20 = float(row.get("price_vs_ema_20", 0) if pd.notna(row.get("price_vs_ema_20", 0)) else 0)
        pv50 = float(row.get("price_vs_ema_50", 0) if pd.notna(row.get("price_vs_ema_50", 0)) else 0)
        pv200 = float(row.get("price_vs_ema_200", 0) if pd.notna(row.get("price_vs_ema_200", 0)) else 0)
        slope50 = float(row.get("ema_50_slope", 0) if pd.notna(row.get("ema_50_slope", 0)) else 0)
        slope200 = float(row.get("ema_200_slope", 0) if pd.notna(row.get("ema_200_slope", 0)) else 0)
        vol_pct = float(row.get("vol_percentile", 50) if pd.notna(row.get("vol_percentile", 50)) else 50)
        vol_exp = float(row.get("vol_expansion", 1) if pd.notna(row.get("vol_expansion", 1)) else 1)
        vol_vs_ma = float(row.get("volume_vs_ma", 1) if pd.notna(row.get("volume_vs_ma", 1)) else 1)
        hh = bool(row.get("hh_hl", False))
        lh = bool(row.get("lh_ll", False))
        div = float(row.get("price_volume_divergence", 0) if pd.notna(row.get("price_volume_divergence", 0)) else 0)
        macd_hist = float(row.get("macd_hist", 0) if pd.notna(row.get("macd_hist", 0)) else 0)

        if rsi > 80 and pv20 > 0.20 and vol_vs_ma > 2.5:
            return Regime.BLOW_OFF
        if dd <= -0.40 and rsi < 30 and vol_pct >= 90:
            return Regime.CAPITULATION
        if -0.15 <= dd <= 0 and rsi > 70 and div > 0 and slope50 <= 0.02:
            return Regime.LATE_BULL
        if -0.15 <= dd <= 0 and 50 <= rsi <= 70 and slope50 < 0 and (lh or div > 0):
            return Regime.DISTRIBUTION
        if pv50 > 0 and pv200 > 0 and slope50 > 0 and slope200 > 0 and 60 <= rsi <= 75 and hh and dd >= -0.15:
            return Regime.BULL_EXPANSION
        if pv50 > 0 and slope50 > 0 and 50 <= rsi <= 65 and -0.40 <= dd <= -0.15:
            return Regime.EARLY_BULL
        if pv50 < 0 and rsi <= 50 and lh and -0.35 <= dd <= -0.15:
            return Regime.EARLY_BEAR
        if -0.40 <= dd <= -0.20 and 45 <= rsi <= 60 and slope50 > 0 and macd_hist > 0:
            return Regime.RECOVERY
        if -0.60 <= dd <= -0.30 and 40 <= rsi <= 55 and vol_exp <= 1.0:
            return Regime.ACCUMULATION
        if abs(pv200) <= 0.15 and 45 <= rsi <= 55 and vol_pct <= 50:
            return Regime.SIDEWAYS
        return Regime.SIDEWAYS

    def classify_series(self, features_df: pd.DataFrame) -> pd.Series:
        """Classify each row without using future rows."""

        return pd.Series(
            [self.classify(features_df, i).value for i in range(len(features_df))],
            index=features_df.index,
            name="regime",
        )
