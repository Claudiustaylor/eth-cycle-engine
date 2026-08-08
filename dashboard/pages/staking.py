"""Staking model — earn yield on your ETH."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import plotly.graph_objects as go
import streamlit as st
import yaml

from dashboard.components.charts import DARK_LAYOUT
from dashboard.components.style import inject_luxury_css

inject_luxury_css()

from dashboard.data_loader import get_results

st.set_page_config(page_title="Staking — ETH Cycle Engine", layout="wide", page_icon="⛏️")

st.title("⛏️ Staking Model")
st.markdown("*Earn yield on your ETH while holding it — like earning interest on a savings account.*")

with st.expander("📖 What is ETH staking?"):
    st.markdown("""
    **Staking** is the process of locking up your ETH to help secure the Ethereum network. In return, you earn more ETH — similar to earning interest on a savings account.

    **How it works:**
    - You deposit ETH into a staking contract
    - The network uses your ETH to validate transactions
    - You earn rewards (currently ~3% APY) paid in ETH
    - Rewards compound — you earn yield on your yield

    **Key concepts:**
    - **Annual Yield**: The % of your staked ETH you earn per year. At 3%, 100 ETH becomes ~103 ETH after a year.
    - **Compounding**: Rewards are added back to your staked balance, so you earn yield on your yield.
    - **Lockup**: Your ETH may be locked for a period. Real Ethereum staking has withdrawal delays.
    - **Slashing Risk**: If your validator misbehaves, a portion of staked ETH can be taken. We assume 0% but real risk exists.
    - **Validator Fees**: Some staking services charge a fee (e.g., exchanges take 10-25% of rewards).

    **This page tracks ETH units separately from USD value** — so you can see how much ETH you're accumulating from staking rewards, independent of ETH's price.
    """)

results = get_results()

if results is None or "staked_eth" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

staked = results["staked_eth"].dropna()
equity = results.get("equity")

# ── Config display ──
st.markdown("### Current Staking Configuration")
with open("config/default.yaml", encoding="utf-8") as fh:
    config = yaml.safe_load(fh)
staking_cfg = config.get("staking", {})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Annual Yield", f"{staking_cfg.get('annual_yield', 0.03) * 100:.1f}%", help="The percentage of your staked ETH you earn per year.")
col2.metric("Validator Fee", f"{staking_cfg.get('validator_fee', 0) * 100:.1f}%", help="Fee charged by the staking service, taken from your rewards.")
col3.metric("Compounding", staking_cfg.get("compounding_frequency", "daily").title(), help="How often rewards are added to your staked balance. Daily = fastest growth.")
col4.metric("% of ETH Staked", f"{staking_cfg.get('pct_staked', 1.0) * 100:.0f}%", help="What portion of your ETH is staked. 100% means all ETH is earning yield.")

st.divider()

# ── Staking over time ──
if staked.sum() > 0:
    st.markdown("### Staked ETH Over Time")
    st.caption("This shows how much ETH was staked during the backtest. If the line is flat at zero, the strategy didn't accumulate enough ETH to stake.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=staked.index, y=staked, name="Staked ETH", line={"color": "#e63946", "width": 2}))
    fig.update_layout(title="Staked ETH Over Time", yaxis_title="ETH Units", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Peak Staked ETH", f"{staked.max():.4f}")
    col_b.metric("Final Staked ETH", f"{staked.iloc[-1]:.4f}")
    estimated_rewards = staked.iloc[-1] * staking_cfg.get("annual_yield", 0.03)
    col_c.metric("Est. Annual Rewards", f"{estimated_rewards:.4f} ETH", help="Approximate ETH you'd earn in rewards per year at current staked amount.")
else:
    st.info("""
    **Staking was enabled but no ETH was staked during the backtest.**

    This happens when the signal-driven strategy didn't generate enough buy signals to accumulate ETH. The strategy may have been in 'neutral' or 'reduce' mode for most of the period.

    Check the Backtest page to see how much ETH was actually accumulated. The staking model still works — it just needs ETH to stake!
    """)

# ── Staking calculator ──
st.divider()
st.markdown("### Interactive Staking Calculator")
st.caption("See how staking grows your ETH over time. Adjust the sliders to model different scenarios.")

col_calc1, col_calc2, col_calc3 = st.columns(3)
eth_amount = col_calc1.number_input("ETH Amount", value=10.0, step=0.1, help="How much ETH you start with.")
annual_yield = col_calc2.slider("Annual Yield (%)", min_value=0.0, max_value=6.0, value=3.0, step=0.1, help="Staking reward rate. Current Ethereum rate is ~3%.")
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
col_r2.metric("Final ETH (after staking)", f"{final_eth:.4f}", help=f"Your ETH after {years_held} years of compounding at {annual_yield}% yield.")
col_r3.metric("Total Staking Rewards", f"{total_rewards:.4f} ETH", help="How much extra ETH you earned from staking. This is in ETH units, not USD.")

fig_growth = go.Figure()
fig_growth.add_trace(go.Scatter(x=list(range(len(eth_history))), y=eth_history, name="ETH with Staking", line={"color": "#e63946", "width": 2}))
fig_growth.add_hline(y=eth_amount, line_color="#666666", line_dash="dash", annotation_text="Without staking")
fig_growth.update_layout(title=f"ETH Growth with {annual_yield}% Staking Yield Over {years_held} Years", xaxis_title="Days", yaxis_title="ETH", **DARK_LAYOUT)
fig_growth.update_layout(height=350)
st.plotly_chart(fig_growth, use_container_width=True)
st.caption("💡 The gap between the purple line and the gray dashed line is your 'free' ETH from staking. Over 10 years at 3%, staking adds ~35% more ETH.")