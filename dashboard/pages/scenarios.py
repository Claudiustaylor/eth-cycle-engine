"""Scenario simulator — what could happen in different market conditions?"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from dashboard.components.style import inject_luxury_css

inject_luxury_css()

from dashboard.data_loader import get_eth_data

st.set_page_config(page_title="Scenarios — ETH Cycle Engine", layout="wide", page_icon="🔮")

st.title("🔮 Scenario Simulator")
st.markdown("*What would your portfolio look like in different market scenarios? Adjust the controls and find out.*")

with st.expander("📖 How does this work?"):
    st.markdown("""
    This simulator uses ETH's **actual historical returns** to build possible future scenarios.

    **Instead of predicting the future, it asks: "What if the market behaves like it did during specific periods?"**

    **Scenario types:**
    - **Historical-like (Random Sample)**: Picks random days from ETH's history — a 'typical' future
    - **Severe Bear**: Uses only the worst daily returns — simulates a prolonged crash
    - **Bear/Base (Bottom Quartile)**: Uses returns from the bottom 25% of days
    - **Moderate Bull (Top Quartile)**: Uses returns from the top 25% of days
    - **Strong Bull**: Uses only the best daily returns — simulates a massive rally
    - **Extreme Historical Repeat**: Replays the exact sequence of historical returns

    **⚠️ Important:** These are **not predictions**. They're stress tests. The 'Severe Bear' scenario is NOT saying "this will happen" — it's saying "IF the market repeats its worst days, here's what your portfolio would look like."

    **The point is to see: Could you survive the worst case?**
    """)

eth = get_eth_data()

if eth is None:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

st.warning("⚠️ Scenario results are based on historical return patterns, NOT forecasts. Extreme scenarios are labeled as non-expected. Do not treat these as predictions.")

returns = eth["close"].pct_change().dropna()

# ── Controls ──
st.markdown("### Configure Your Simulation")

col1, col2 = st.columns(2)
horizon_years = col1.slider("Time Horizon (years)", min_value=1, max_value=10, value=5, help="How many years into the future to simulate.")
n_simulations = col2.slider("Number of Simulations", min_value=100, max_value=5000, value=1000, step=100, help="More simulations = smoother results but slower. 1000 is a good balance.")

horizon_days = horizon_years * 365

st.markdown("### Choose a Scenario Type")
st.caption("Pick a scenario to see how your portfolio would perform under those market conditions.")

scenario_type = st.selectbox(
    "Scenario",
    [
        "Historical-like (Random Sample)",
        "Severe Bear (Worst Returns)",
        "Bear/Base (Bottom Quartile)",
        "Moderate Bull (Top Quartile)",
        "Strong Bull (Best Returns)",
        "Extreme Historical Repeat",
    ],
    index=0,
)

rng = np.random.default_rng(42)
n = n_simulations
h = min(horizon_days, len(returns))
clean = returns.to_numpy()

if "Severe" in scenario_type or "Bear" in scenario_type:
    sample_pool = np.sort(clean)[:h]
    sims = rng.choice(sample_pool, size=(n, h), replace=True)
elif "Bull" in scenario_type:
    sample_pool = np.sort(clean)[-h:]
    sims = rng.choice(sample_pool, size=(n, h), replace=True)
elif "Extreme" in scenario_type:
    sims = np.array([clean] * n)
else:
    sims = rng.choice(clean, size=(n, h), replace=True)

paths = np.cumprod(1 + sims, axis=1)
finals = paths[:, -1]

# ── Results ──
st.divider()
st.markdown("### Simulation Results")
st.caption(f"{n_simulations:,} simulated {horizon_years}-year paths under '{scenario_type}' conditions. 1x = breakeven (no gain, no loss).")

col1m, col2m, col3m, col4m, col5m = st.columns(5)
col1m.metric("Worst 10% (P10)", f"{np.percentile(finals, 10):.2f}x", help="1-in-10 futures are this bad or worse. Below 1x = losing money.")
col2m.metric("P25", f"{np.percentile(finals, 25):.2f}x")
col3m.metric("Median (P50)", f"{np.median(finals):.2f}x", help="The middle outcome. 50% of futures are better, 50% are worse.")
col4m.metric("P75", f"{np.percentile(finals, 75):.2f}x")
col5m.metric("Best 10% (P90)", f"{np.percentile(finals, 90):.2f}x", help="1-in-10 futures are this good or better.")

# ── Distribution ──
st.markdown("### Distribution of Outcomes")
st.caption("How are the simulated final portfolio values spread out? The red dashed line at 1x = breakeven. Everything left of it = losing money.")
fig = px.histogram(finals, nbins=50, title=f"Final Portfolio Multiple Distribution — {scenario_type}", labels={"value": "Multiple (1x = breakeven)"})
fig.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#121212", font={"color": "#f5f5f5"}, height=350)
fig.add_vline(x=1.0, line_color="#ef4444", line_dash="dash", annotation_text="Breakeven")
st.plotly_chart(fig, use_container_width=True)

# ── Sample paths ──
st.markdown("### Sample Simulation Paths")
st.caption(f"Here are {min(50, n)} of the {n:,} simulated paths. Each line is one possible future. The spread shows how uncertain outcomes are.")
sample_n = min(50, n)
fig_paths = go.Figure()
for i in range(sample_n):
    fig_paths.add_trace(go.Scatter(x=list(range(h)), y=paths[i], mode="lines", line={"width": 0.5}, opacity=0.3, showlegend=False))
fig_paths.add_hline(y=1.0, line_color="#666666", line_dash="dash", annotation_text="Breakeven")
fig_paths.update_layout(title=f"{sample_n} Random Simulation Paths", xaxis_title="Days", yaxis_title="Portfolio Multiple (1x = start)", **DARK_LAYOUT)
fig_paths.update_layout(height=400)
st.plotly_chart(fig_paths, use_container_width=True)

# ── Probabilities ──
st.divider()
st.markdown("### Probability Summary")
st.caption("Key probabilities to help you understand the risk/reward profile.")

col_p1, col_p2, col_p3, col_p4 = st.columns(4)
col_p1.metric("Probability of Loss", f"{(finals < 1).mean() * 100:.1f}%", help="% of simulations where you end up with less than you started.")
col_p2.metric("Probability of 2x Return", f"{(finals >= 2).mean() * 100:.1f}%", help="% of simulations where you double your money.")
col_p3.metric("Probability of 5x Return", f"{(finals >= 5).mean() * 100:.1f}%", help="% of simulations where you 5x your money.")
dd_all = paths / np.maximum.accumulate(paths, axis=1) - 1
col_p4.metric("Probability of 50%+ Crash", f"{(dd_all.min(axis=1) <= -0.5).mean() * 100:.1f}%", help="% of simulations where your portfolio drops 50%+ from peak at some point.")