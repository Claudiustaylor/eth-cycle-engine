"""Anomaly detection and defensive-mode policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class AnomalyState:
    """Detected anomaly state."""

    is_anomaly: bool
    reasons: list[str]
    severity: float


class AnomalyDetector:
    """Detect large market anomalies from trailing features."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.cfg = config.get("risk", {}).get("anomaly", {})

    def detect(self, features_df: pd.DataFrame, idx: int) -> AnomalyState:
        """Detect anomaly at idx using only historical rows."""

        hist = features_df.iloc[: idx + 1]
        row = hist.iloc[-1]
        reasons: list[str] = []
        ret = float(row.get("returns", 0) if pd.notna(row.get("returns", 0)) else 0)
        std = hist["returns"].rolling(60, min_periods=20).std().iloc[-1] if "returns" in hist else 0
        z = abs(ret / std) if std and pd.notna(std) else 0
        if z > float(self.cfg.get("return_zscore_threshold", 4.0)):
            reasons.append(f"return z-score {z:.1f}")
        if float(row.get("vol_percentile", 0) or 0) > float(self.cfg.get("vol_percentile_threshold", 95)):
            reasons.append("volatility percentile extreme")
        if float(row.get("volume_vs_ma", 0) or 0) > float(self.cfg.get("volume_spike_multiple", 5.0)):
            reasons.append("volume spike")
        return AnomalyState(bool(reasons), reasons, min(1.0, len(reasons) / 3))

    def anomaly_action(self, anomaly_state: AnomalyState) -> dict[str, float | bool]:
        """Return defensive action for anomaly state."""

        reduction = float(self.cfg.get("defensive_reduction", 0.50)) * anomaly_state.severity
        return {
            "reduce_position": reduction,
            "suspend_entries": anomaly_state.is_anomaly,
            "widen_stops": 2.0 if anomaly_state.is_anomaly else 1.0,
            "defensive_mode": anomaly_state.is_anomaly,
        }
