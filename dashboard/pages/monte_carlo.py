"""Monte Carlo simulation — what could the future look like?"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT, monte_carlo_chart

st.set_page_config(page_title="Monte Carlo — ETH Cycle Engine", layout="wide", page_icon="🎲")

from dashboard.components.style import inject_luxury_css
inject_luxury_css()

st.title("🎲 Monte Carlo Simulation")
st.markdown("*What are the possible futures for your portfolio? Instead of one prediction, we simulate thousands.*")

with st.expander("📖 What is Monte Carlo simulation?"):
    st.markdown("""
    **Think of it like rolling dice, but for your investment.**

    Instead of saying "ETH will return 30% next year" (which is a guess), Monte Carlo runs **2,000 possible futures** based on how ETH has actually behaved in the past.

    **How it works:**
    1. Take ETH's historical daily returns (real data)
    2. Randomly pick returns to build 2,000 possible 1-year paths
    3. Track how your portfolio would perform in each scenario
    4. Report the range of outcomes

    **Key outputs explained:**
    - **P10 (Worst 10%)**: In 1-out-of-10 futures, your portfolio does this badly or worse
    - **P50 (Median)**: The middle outcome — 50% of futures are better, 50% are worse
    - **P90 (Best 10%)**: In 1-out-of-10 futures, your portfolio does this well or better
    - **P(Loss)**: What % of futures result in losing money
    - **P(50%+ Drawdown)**: What % of futures involve your portfolio being cut in half at some point

    **Important:** This is NOT a prediction. It shows the *range* of plausible outcomes based on historical patterns. The future can be better or worse than anything we've seen before.
    """)

report_path = Path("output/report.json")
if not report_path.exists():
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

report = json.loads(report_path.read_text())
mc_data = report.get("monte_carlo", {})

if not mc_data:
    st.warning("No Monte Carlo results available.")
    st.stop()

# ── Key metrics ──
st.markdown("### The Range of Outcomes")
st.caption("Based on 2,000 simulated 1-year futures. 1x = breakeven (no gain, no loss).")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Median Outcome", f"{mc_data.get('p50', 0):.2f}x", help="The middle outcome. 50% of futures are better, 50% are worse. Above 1x = profitable.")
col2.metric("Worst 10% (P10)", f"{mc_data.get('p10', 0):.2f}x", help="1-in-10 chance of this or worse. Below 1x = losing money.")
col3.metric("Best 10% (P90)", f"{mc_data.get('p90', 0):.2f}x", help="1-in-10 chance of this or better.")
col4.metric("Probability of Loss", f"{mc_data.get('prob_loss', 0) * 100:.1f}%", help="% of simulated futures where you lose money.")
col5.metric("P(50%+ Drawdown)", f"{mc_data.get('prob_drawdown_50', 0) * 100:.1f}%", help="% of futures where your portfolio drops 50%+ from peak at some point.")

st.divider()

# ── Charts ──
col_left, col_right = st.columns(2)
with col_left:
    st.markdown("#### Outcome Distribution")
    st.caption("The range of possible final portfolio values after 1 year.")
    st.plotly_chart(monte_carlo_chart(mc_data), use_container_width=True)
with col_right:
    st.markdown("#### Probability Summary")
    fig = go.Figure()
    targets = [
        ("P(Loss)", mc_data.get("prob_loss", 0) * 100, "#ef4444"),
        ("P(2x Return)", mc_data.get("prob_target", 0) * 100, "#22c55e"),
        ("P(50%+ DD)", mc_data.get("prob_drawdown_50", 0) * 100, "#f59e0b"),
    ]
    fig.add_trace(go.Bar(x=[t[0] for t in targets], y=[t[1] for t in targets], marker_color=[t[2] for t in targets]))
    fig.update_layout(title="Probability of Key Outcomes (%)", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# ── Full results ──
st.markdown("### Full Simulation Results")
st.json(mc_data)

# ── Robustness ──
st.divider()
st.markdown("### Is the Strategy's Edge Real or Just Luck?")
st.caption("This test reshuffles the daily returns 500 times and checks if the strategy's performance could have happened by chance.")

robustness = report.get("robustness", {})
if robustness:
    col_r1, col_r2 = st.columns(2)
    col_r1.metric("Robustness Rating", robustness.get("rating", "N/A").upper(), help="Strong = the edge is real. Weak/Moderate = uncertain. Likely Overfit = the strategy only works on historical data.")
    col_r2.metric("Statistical P-value", f"{robustness.get('mc', {}).get('p_value', 0):.4f}", help="Below 0.05 = the edge is statistically significant. Above 0.10 = could be random luck.")

    st.info(f"**What this means:** {robustness.get('explanation', 'N/A')}")

    actual_sharpe = robustness.get("mc", {}).get("actual_sharpe", 0)
    p_value = robustness.get("mc", {}).get("p_value", 0)
    st.metric("Actual Sharpe Ratio", f"{actual_sharpe:.4f}", help="The strategy's real Sharpe ratio.")

    if p_value < 0.05:
        st.success("✅ **Statistically significant** — The strategy's performance is unlikely to be random luck (p < 0.05).")
    elif p_value < 0.10:
        st.warning("⚠️ **Marginally significant** — The edge may exist but needs more validation (p < 0.10).")
    else:
        st.error("❌ **NOT statistically significant** — The strategy's performance could be random luck (p ≥ 0.10). This doesn't mean it's useless, but you shouldn't trust it blindly.")