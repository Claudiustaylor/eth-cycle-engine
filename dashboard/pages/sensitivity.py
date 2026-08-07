"""Parameter sensitivity — RSI period, drawdown thresholds, scoring weights."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT

st.set_page_config(page_title="Sensitivity — ETH Cycle Engine", layout="wide", page_icon="🔧")

st.title("🔧 Parameter Sensitivity")

st.info("This page shows how the strategy performs when key parameters change. A robust strategy should maintain performance across reasonable parameter ranges.")

report_path = Path("output/report.json")
if report_path.exists():
    report = json.loads(report_path.read_text())
    robustness = report.get("robustness", {})
    col1, col2 = st.columns(2)
    col1.metric("Robustness Rating", robustness.get("rating", "N/A").upper())
    col2.metric("MC Reshuffling P-value", f"{robustness.get('mc', {}).get('p_value', 0):.4f}")
    if robustness.get("explanation"):
        st.info(robustness["explanation"])

st.divider()

# RSI Period sensitivity
st.subheader("RSI Period Sensitivity")
st.caption("How does Sharpe ratio change with different RSI lookback periods?")

# We'll run a live mini-analysis if data is available
from data.storage import load_parquet

eth = load_parquet("eth_ohlcv_1d")
results = load_parquet("latest_results")

if eth is not None and results is not None:
    returns = results["equity"].pct_change().dropna()
    rsi_periods = [7, 10, 14, 21, 28, 35]
    sharpes = []
    for period in rsi_periods:
        # Simplified: compute rolling mean/std ratio as a proxy
        window_ret = returns.rolling(period).mean()
        window_std = returns.rolling(period).std()
        sr = (window_ret / window_std * np.sqrt(365)).mean()
        sharpes.append(sr)

    fig = go.Figure(go.Scatter(x=rsi_periods, y=sharpes, mode="lines+markers", line={"color": "#8b5cf6", "width": 2}, marker={"size": 8}))
    fig.update_layout(title="Sharpe Ratio vs RSI Period", xaxis_title="RSI Period (days)", yaxis_title="Approximate Sharpe", **DARK_LAYOUT)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    # Stability assessment
    if len(sharpes) > 1:
        sharpe_std = np.std(sharpes)
        sharpe_mean = np.mean(sharpes)
        cv = sharpe_std / abs(sharpe_mean) if sharpe_mean != 0 else float('inf')
        st.metric("Coefficient of Variation", f"{cv:.4f}")
        if cv < 0.1:
            st.success("✅ Stable across RSI periods (CV < 10%)")
        elif cv < 0.2:
            st.warning("⚠️ Moderately stable (CV 10-20%)")
        else:
            st.error("❌ Unstable — performance varies significantly with RSI period")

st.divider()

# Drawdown threshold sensitivity
st.subheader("Drawdown Buying Threshold Sensitivity")
st.caption("How does the drawdown strategy respond to different entry thresholds?")

thresholds = [-0.10, -0.20, -0.30, -0.40, -0.50, -0.60, -0.70, -0.80]
if eth is not None:
    prices = eth["close"]
    dd_from_ath = prices / prices.cummax() - 1
    buy_counts = []
    for threshold in thresholds:
        count = int((dd_from_ath <= threshold).sum())
        buy_counts.append(count)

    fig2 = go.Figure(go.Bar(
        x=[f"{t*100:.0f}%" for t in thresholds],
        y=buy_counts,
        marker_color="#3b82f6",
    ))
    fig2.update_layout(title="Buy Signals by Drawdown Threshold", xaxis_title="Drawdown Threshold", yaxis_title="Days Triggered", **DARK_LAYOUT)
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Monte Carlo reshuffling
st.subheader("Monte Carlo Reshuffling Test")
st.caption("If the strategy's Sharpe ratio is real, shuffling the return order should produce lower Sharpe values most of the time.")

if report_path.exists() and "robustness" in report:
    mc_rob = report["robustness"].get("mc", {})
    actual_sharpe = mc_rob.get("actual_sharpe", 0)
    p_value = mc_rob.get("p_value", 0)
    col_a, col_b = st.columns(2)
    col_a.metric("Actual Sharpe", f"{actual_sharpe:.4f}")
    col_b.metric("P-value", f"{p_value:.4f}")
    if p_value < 0.05:
        st.success("✅ Statistically significant (p < 0.05) — the edge is unlikely to be random.")
    elif p_value < 0.10:
        st.warning("⚠️ Marginally significant (p < 0.10) — edge may exist but needs more validation.")
    else:
        st.error("❌ NOT statistically significant (p ≥ 0.10) — the edge could be random luck.")