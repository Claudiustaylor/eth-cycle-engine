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

report_path = Path("output/report.json")
if not report_path.exists():
    st.warning("No results found. Run `python example_backtest.py` first.")
    st.stop()

report = json.loads(report_path.read_text())
strategy_data = report.get("strategy", {})
benchmark_data = report.get("benchmarks", {})

all_strategies = {"Signal Driven": strategy_data, **benchmark_data}

# Metrics table
st.subheader("Performance Metrics")
metrics = ["cagr", "total_return", "max_drawdown", "sharpe_ratio", "sortino_ratio", "calmar_ratio", "num_trades", "final_portfolio_value"]
display_names = ["CAGR", "Total Return", "Max DD", "Sharpe", "Sortino", "Calmar", "Trades", "Final Value"]

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

st.divider()

# Charts
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(strategy_comparison_chart(all_strategies), use_container_width=True)
with col2:
    # CAGR comparison
    names = list(all_strategies.keys())
    cagr_vals = [all_strategies[n].get("cagr", 0) for n in names]
    fig = go.Figure(go.Bar(x=names, y=[c * 100 for c in cagr_vals], marker_color="#8b5cf6"))
    fig.update_layout(title="CAGR Comparison (%)", **DARK_LAYOUT)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# Max drawdown comparison
st.subheader("Max Drawdown Comparison")
dd_vals = [all_strategies[n].get("max_drawdown", 0) * 100 for n in names]
fig_dd = go.Figure(go.Bar(x=names, y=dd_vals, marker_color="#ff3860"))
fig_dd.update_layout(title="Max Drawdown (%) — Lower is Better", **DARK_LAYOUT)
fig_dd.update_layout(height=350)
st.plotly_chart(fig_dd, use_container_width=True)

# Final value comparison
st.subheader("Final Portfolio Value")
final_vals = [all_strategies[n].get("final_portfolio_value", 0) for n in names]
fig_fv = go.Figure(go.Bar(x=names, y=final_vals, marker_color="#00d68f"))
fig_fv.update_layout(title="Final Portfolio Value ($)", **DARK_LAYOUT)
fig_fv.update_layout(height=350)
st.plotly_chart(fig_fv, use_container_width=True)