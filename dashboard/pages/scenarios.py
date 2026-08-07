"""Scenario simulator — historical return scenarios across time horizons."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from data.storage import load_parquet

st.set_page_config(page_title="Scenarios — ETH Cycle Engine", layout="wide", page_icon="🔮")

st.title("🔮 Scenario Simulator")

eth = load_parquet("eth_ohlcv_1d")

if eth is None:
    st.warning("No data found. Run `python example_backtest.py` first.")
    st.stop()

st.info("Scenario results are historical return resamples, NOT forecasts. Extreme repeats are labeled as non-expected.")

returns = eth["close"].pct_change().dropna()

# Controls
col1, col2 = st.columns(2)
horizon_years = col1.slider("Time Horizon (years)", min_value=1, max_value=10, value=5)
n_simulations = col2.slider("Simulations", min_value=100, max_value=5000, value=1000, step=100)

horizon_days = horizon_years * 365

# Scenario selection
st.divider()
st.subheader("Scenario Type")
scenario_type = st.selectbox(
    "Select scenario",
    ["Historical-like (random sample)", "Severe Bear (worst returns)", "Bear/Base (bottom quartile)", "Moderate Bull (top quartile)", "Strong Bull (best returns)", "Extreme Historical Repeat"],
    index=0,
)

rng = np.random.default_rng(42)
n = n_simulations
h = min(horizon_days, len(returns))
clean = returns.to_numpy()

if "Severe" in scenario_type or "Bear" in scenario_type:
    sample_pool = np.sort(clean)[:h]  # worst returns
    sims = rng.choice(sample_pool, size=(n, h), replace=True)
elif "Bull" in scenario_type:
    sample_pool = np.sort(clean)[-h:]  # best returns
    sims = rng.choice(sample_pool, size=(n, h), replace=True)
elif "Extreme" in scenario_type:
    sims = np.array([clean.values if hasattr(clean, 'values') else clean] * n)  # replay actual history
else:
    sims = rng.choice(clean, size=(n, h), replace=True)

# Compute paths
paths = np.cumprod(1 + sims, axis=1)
finals = paths[:, -1]

# Percentiles
col1m, col2m, col3m, col4m, col5m = st.columns(5)
col1m.metric("P10 (Worst 10%)", f"{np.percentile(finals, 10):.2f}x")
col2m.metric("P25", f"{np.percentile(finals, 25):.2f}x")
col3m.metric("Median", f"{np.median(finals):.2f}x")
col4m.metric("P75", f"{np.percentile(finals, 75):.2f}x")
col5m.metric("P90 (Best 10%)", f"{np.percentile(finals, 90):.2f}x")

# Distribution
st.divider()
import plotly.express as px

fig = px.histogram(finals, nbins=50, title=f"Final Portfolio Multiple Distribution ({scenario_type})", labels={"value": "Multiple (1x = breakeven)"})
fig.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=350)
fig.add_vline(x=1.0, line_color="#ff3860", line_dash="dash", annotation_text="Breakeven")
st.plotly_chart(fig, use_container_width=True)

# Sample paths
st.subheader("Sample Simulation Paths")
sample_n = min(50, n)
fig_paths = go.Figure()
for i in range(sample_n):
    fig_paths.add_trace(go.Scatter(x=list(range(h)), y=paths[i], mode="lines", line={"width": 0.5}, opacity=0.3, showlegend=False))
fig_paths.add_hline(y=1.0, line_color="#6b7280", line_dash="dash", annotation_text="Breakeven")
fig_paths.update_layout(title=f"{sample_n} Random Simulation Paths", xaxis_title="Days", yaxis_title="Portfolio Multiple", **DARK_LAYOUT)
fig_paths.update_layout(height=400)
st.plotly_chart(fig_paths, use_container_width=True)

# Probability metrics
st.divider()
st.subheader("Probability Outcomes")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
col_p1.metric("P(Loss)", f"{(finals < 1).mean() * 100:.1f}%")
col_p2.metric("P(2x return)", f"{(finals >= 2).mean() * 100:.1f}%")
col_p3.metric("P(5x return)", f"{(finals >= 5).mean() * 100:.1f}%")
# Max drawdown across all paths
dd_all = paths / np.maximum.accumulate(paths, axis=1) - 1
col_p4.metric("P(50%+ DD)", f"{(dd_all.min(axis=1) <= -0.5).mean() * 100:.1f}%")