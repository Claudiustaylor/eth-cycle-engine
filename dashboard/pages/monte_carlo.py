"""Monte Carlo simulation results."""

from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT, monte_carlo_chart

st.set_page_config(page_title="Monte Carlo — ETH Cycle Engine", layout="wide", page_icon="🎲")

st.title("🎲 Monte Carlo Simulation")

report_path = Path("output/report.json")
if not report_path.exists():
    st.warning("No results found. Run `python example_backtest.py` first.")
    st.stop()

report = json.loads(report_path.read_text())
mc_data = report.get("monte_carlo", {})

if not mc_data:
    st.warning("No Monte Carlo results in report. Run the example backtest first.")
    st.stop()

# Key metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Median Outcome", f"{mc_data.get('p50', 0):.2f}x")
col2.metric("P10 (Worst 10%)", f"{mc_data.get('p10', 0):.2f}x")
col3.metric("P90 (Best 10%)", f"{mc_data.get('p90', 0):.2f}x")
col4.metric("P(Loss)", f"{mc_data.get('prob_loss', 0) * 100:.1f}%")
col5.metric("P(50%+ Drawdown)", f"{mc_data.get('prob_drawdown_50', 0) * 100:.1f}%")

st.divider()

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(monte_carlo_chart(mc_data), use_container_width=True)
with col_right:
    # Probability bars
    fig = go.Figure()
    targets = [
        ("P(Loss)", mc_data.get("prob_loss", 0) * 100, "#ff3860"),
        ("P(2x target)", mc_data.get("prob_target", 0) * 100, "#00d68f"),
        ("P(50%+ DD)", mc_data.get("prob_drawdown_50", 0) * 100, "#f59e0b"),
    ]
    fig.add_trace(go.Bar(x=[t[0] for t in targets], y=[t[1] for t in targets], marker_color=[t[2] for t in targets]))
    fig.update_layout(title="Probability Outcomes (%)", **DARK_LAYOUT)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# Full results table
st.subheader("Full Monte Carlo Results")
st.json(mc_data)

# Robustness
st.divider()
st.subheader("Robustness Analysis")
robustness = report.get("robustness", {})
if robustness:
    col_r1, col_r2 = st.columns(2)
    col_r1.metric("Rating", robustness.get("rating", "N/A").upper())
    col_r2.metric("MC P-value", f"{robustness.get('mc', {}).get('p_value', 0):.4f}")
    st.info(f"Explanation: {robustness.get('explanation', 'N/A')}")
    actual_sharpe = robustness.get("mc", {}).get("actual_sharpe", 0)
    st.metric("Actual Sharpe Ratio", f"{actual_sharpe:.4f}")