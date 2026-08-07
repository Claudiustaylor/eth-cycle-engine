"""Signal explanation generation."""

from __future__ import annotations

import pandas as pd

from regimes.types import Regime


class SignalExplainer:
    """Generate human-readable, value-specific signal explanations."""

    def explain(
        self,
        sub_scores: dict[str, float],
        combined_score: float,
        features_df: pd.DataFrame,
        idx: int,
        regime: Regime | str,
        action: str,
    ) -> str:
        """Return a multi-line signal explanation."""

        row = features_df.iloc[idx]
        reasons: list[str] = []
        if pd.notna(row.get("drawdown_cycle", pd.NA)):
            reasons.append(f"ETH is {abs(float(row['drawdown_cycle'])):.0%} below cycle high.")
        if pd.notna(row.get("rsi", pd.NA)):
            reasons.append(f"RSI is {float(row['rsi']):.1f}, showing current momentum state.")
        if "funding_rate_percentile" in row and pd.notna(row.get("funding_rate_percentile")):
            reasons.append(f"Funding percentile is {float(row['funding_rate_percentile']):.1f}.")
        if "exchange_outflow_percentile" in row and pd.notna(row.get("exchange_outflow_percentile")):
            reasons.append(f"Exchange outflow percentile is {float(row['exchange_outflow_percentile']):.1f}.")
        if pd.notna(row.get("price_vs_ema_200", pd.NA)):
            reasons.append(f"Price is {float(row['price_vs_ema_200']):.1%} versus the 200-day EMA.")
        if pd.notna(row.get("risk_on_off", pd.NA)):
            reasons.append(f"Macro risk score is {float(row['risk_on_off']):.1f}/100.")
        if pd.notna(row.get("vol_percentile", pd.NA)):
            reasons.append(f"Realized volatility percentile is {float(row['vol_percentile']):.1f}.")
        regime_value = regime.value if isinstance(regime, Regime) else str(regime)
        lines = [
            f"SIGNAL CONFIDENCE: {combined_score:.0f}/100",
            f"REGIME: {regime_value}",
            "",
            "REASONS:",
            *[f"- {reason}" for reason in reasons],
            "",
            "SUB-SCORES:",
        ]
        labels = {
            "valuation": "Valuation",
            "trend": "Trend",
            "momentum": "Momentum",
            "volatility": "Volatility",
            "derivatives": "Derivatives",
            "onchain": "On-Chain",
            "macro": "Macro",
            "regime": "Regime",
        }
        lines.extend(f"  {labels.get(k, k.title()):<12} {v:.0f}/100" for k, v in sub_scores.items())
        lines.extend(["", f"RECOMMENDED ACTION: {action}."])
        return "\n".join(lines)
