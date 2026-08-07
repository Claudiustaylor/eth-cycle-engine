"""Staking model — yield, rewards, ETH units, USD value."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from data.storage import load_parquet

st.set_page_config(page_title="Staking — ETH Cycle Engine", layout="wide", page_icon="⛏️")

st.title("⛏️ Staking Model")

results = load_parquet("latest_results")

if results is None or "staked_eth" not in results:
    st.warning("No backtest results found. Run `python example_backtest.py` first.")
    st.stop()

staked = results["staked_eth"].dropna()
eth_holdings = results.get("eth_holdings", pd.Series(dtype=float))
equity = results.get("equity", pd.Series(dtype=float))

# Config display
st.subheader("Staking Configuration")
import yaml

config = yaml.safe_load(open("config/default.yaml"))
staking_cfg = config.get("staking", {})
col1, col2, col3, col4 = st.columns(4)
col1.metric("Annual Yield", f"{staking_cfg.get('annual_yield', 0.03) * 100:.1f}%")
col2.metric("Validator Fee", f"{staking_cfg.get('validator_fee', 0) * 100:.1f}%")
col3.metric("Compounding", staking_cfg.get("compounding_frequency", "daily").title())
col4.metric("Pct Staked", f"{staking_cfg.get('pct_staked', 1.0) * 100:.0f}%")

st.divider()

# Staking over time
if staked.sum() > 0:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=staked.index, y=staked, name="Staked ETH", line={"color": "#8b5cf6", "width": 2}))
    fig.update_layout(title="Staked ETH Over Time", yaxis_title="ETH Units", **DARK_LAYOUT)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Key metrics
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Peak Staked ETH", f"{staked.max():.4f}")
    col_b.metric("Final Staked ETH", f"{staked.iloc[-1]:.4f}")
    # Estimate rewards (simplified)
    if equity is not None and len(equity) > 0:
        estimated_rewards = staked.iloc[-1] * staking_cfg.get("annual_yield", 0.03) if len(staked) > 0 else 0
        col_c.metric("Est. Annual Rewards", f"{estimated_rewards:.4f} ETH")
else:
    st.info("Staking was enabled but no ETH was staked during the backtest period.")
    st.write("This can happen if the signal strategy didn't generate enough buy signals to accumulate ETH, or if staking is disabled in config.")
    st.write("Check `config/default.yaml` → `staking.enabled: true`")

# Staking yield calculator
st.divider()
st.subheader("Staking Yield Calculator")

col_calc1, col_calc2, col_calc3 = st.columns(3)
eth_amount = col_calc1.number_input("ETH Amount", value=10.0, step=0.1)
annual_yield = col_calc2.slider("Annual Yield (%)", min_value=0.0, max_value=6.0, value=3.0, step=0.1)
years_held = col_calc3.slider("Years Held", min_value=1, max_value=10, value=5)

daily_rate = (annual_yield / 100) / 365
total_eth = eth_amount
eth_history = [total_eth]
for _day in range(int(years_held * 365)):
    reward = total_eth * daily_rate
    total_eth += reward
    eth_history.append(total_eth)

final_eth = total_eth
total_rewards = final_eth - eth_amount

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Starting ETH", f"{eth_amount:.4f}")
col_r2.metric("Final ETH (after staking)", f"{final_eth:.4f}")
col_r3.metric("Total Staking Rewards", f"{total_rewards:.4f} ETH")

# Growth chart
fig_growth = go.Figure()
fig_growth.add_trace(go.Scatter(x=list(range(len(eth_history))), y=eth_history, name="ETH w/ Staking", line={"color": "#8b5cf6", "width": 2}))
fig_growth.add_hline(y=eth_amount, line_color="#6b7280", line_dash="dash", annotation_text="No staking")
fig_growth.update_layout(title=f"ETH Growth with {annual_yield}% Staking Yield Over {years_held} Years", xaxis_title="Days", yaxis_title="ETH", **DARK_LAYOUT)
fig_growth.update_layout(height=350)
st.plotly_chart(fig_growth, use_container_width=True)