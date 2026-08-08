"""Strategy comparison — all strategies side by side."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT, strategy_comparison_chart

st.set_page_config(page_title="Comparison — ETH Cycle Engine", layout="wide", page_icon="⚖️")

st.title("⚖️ Strategy Comparison")
st.markdown("*How does the signal-driven strategy stack up against simpler approaches?*")

with st.expander("📖 What are we comparing?"):
    st.markdown("""
    This page compares 7 different approaches to investing in ETH:

    1. **Signal Driven** — Our main strategy. Uses the 0-100 confidence score to decide when to buy and sell.
    2. **Buy and Hold** — Buy ETH on day 1, never sell. The simplest benchmark.
    3. **Buy and Hold + Staking** — Same, but also earns staking yield (like interest).
    4. **Dollar Cost Averaging (DCA)** — Buy a fixed dollar amount at regular intervals, regardless of price.
    5. **200-Day Moving Average** — Buy when price is above the 200-day average, sell when below. A classic trend-following rule.
    6. **Simple Drawdown Buying** — Buy when ETH drops 20%+ from its high. A simple "buy the dip" approach.

    **What to look for:**
    - Does the signal strategy beat buy-and-hold? (It should, or why bother?)
    - Does it have a smaller max drawdown? (Less pain)
    - Does it have a better Sharpe ratio? (Better risk-adjusted returns)
    - Sometimes simple strategies (like the 200-day MA) outperform complex ones — that's okay, it's the truth.
    """)

report_path = Path("output/report.json")
if not report_path.exists():
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

report = json.loads(report_path.read_text())
strategy_data = report.get("strategy", {})
benchmark_data = report.get("benchmarks", {})

all_strategies = {"Signal Driven": strategy_data, **benchmark_data}

# ── Metrics table ──
st.markdown("### Performance Comparison Table")

metrics = ["cagr", "total_return", "max_drawdown", "sharpe_ratio", "sortino_ratio", "calmar_ratio", "num_trades", "final_portfolio_value"]
display_names = ["CAGR", "Total Return", "Max Drawdown", "Sharpe", "Sortino", "Calmar", "Trades", "Final Value"]

rows = []
for name, data in all_strategies.items():
    row = {"Strategy": name}
    for metric, display in zip(metrics, display_names, strict=False):
        val = data.get(metric, 0)
        if metric == "final_portfolio_value":
            row[display] = f"${val:,.0f}"
        elif metric == "num_trades":
            row[display] = f"{val:.0f}"
        else:
            row[display] = f"{val:.4f}" if abs(val) < 100 else f"{val:.2f}"
    rows.append(row)

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption("💡 **CAGR** = yearly growth rate | **Max DD** = worst drop from peak | **Sharpe** = return per unit risk (>1.0 is good) | **Sortino** = like Sharpe but only counts bad volatility")

st.divider()

# ── Charts ──
st.markdown("### Visual Comparison")
st.caption("Higher is better for CAGR, Sharpe, and Final Value. Lower is better for Max Drawdown.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Sharpe Ratio (higher = better)")
    st.caption("Measures return per unit of risk. Above 1.0 is good.")
    st.plotly_chart(strategy_comparison_chart(all_strategies), use_container_width=True)
with col2:
    st.markdown("#### CAGR (higher = better)")
    st.caption("Compound Annual Growth Rate — average yearly return.")
    names = list(all_strategies.keys())
    cagr_vals = [all_strategies[n].get("cagr", 0) for n in names]
    fig = go.Figure(go.Bar(x=names, y=[c * 100 for c in cagr_vals], marker_color="#8b5cf6"))
    fig.update_layout(title="CAGR (%)", **DARK_LAYOUT)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("#### Max Drawdown (lower magnitude = better)")
st.caption("The worst peak-to-trough decline. A smaller bar means less pain. This is arguably the most important metric for real-world investing.")
dd_vals = [all_strategies[n].get("max_drawdown", 0) * 100 for n in names]
fig_dd = go.Figure(go.Bar(x=names, y=dd_vals, marker_color="#ff3860"))
fig_dd.update_layout(title="Max Drawdown (%)", **DARK_LAYOUT)
fig_dd.update_layout(height=350)
st.plotly_chart(fig_dd, use_container_width=True)

st.markdown("#### Final Portfolio Value (higher = better)")
st.caption(f"What your $50,000 became. Best performer: **${max(all_strategies[n].get('final_portfolio_value', 0) for n in names):,.0f}**")
final_vals = [all_strategies[n].get("final_portfolio_value", 0) for n in names]
fig_fv = go.Figure(go.Bar(x=names, y=final_vals, marker_color="#00d68f"))
fig_fv.update_layout(title="Final Value ($)", **DARK_LAYOUT)
fig_fv.update_layout(height=350)
st.plotly_chart(fig_fv, use_container_width=True)