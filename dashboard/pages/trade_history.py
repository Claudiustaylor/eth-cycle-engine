"""Trade history — full trade log from backtest."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from data.storage import load_parquet

st.set_page_config(page_title="Trade History — ETH Cycle Engine", layout="wide", page_icon="📋")

st.title("📋 Trade History")

results = load_parquet("latest_results")
eth = load_parquet("eth_ohlcv_1d")

if results is None or "equity" not in results:
    st.warning("No backtest results found. Run `python example_backtest.py` first.")
    st.stop()

equity = results["equity"].dropna()
returns = equity.pct_change().dropna()

# Summary
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Bars", f"{len(equity)}")
positive_days = (returns > 0).sum()
col2.metric("Positive Days", f"{positive_days} ({positive_days / len(returns) * 100:.1f}%)")
negative_days = (returns < 0).sum()
col3.metric("Negative Days", f"{negative_days} ({negative_days / len(returns) * 100:.1f}%)")
best_day = returns.max() * 100
col4.metric("Best Day", f"+{best_day:.1f}%")

st.divider()

# Daily returns over time
st.subheader("Daily Returns Over Time")
fig = go.Figure()
colors = ["#00d68f" if r > 0 else "#ff3860" for r in returns]
fig.add_trace(go.Bar(x=returns.index, y=returns * 100, marker_color=colors, name="Daily Return %"))
fig.update_layout(title="Daily Strategy Returns (%)", yaxis_title="Return %", **DARK_LAYOUT)
fig.update_layout(height=350)
st.plotly_chart(fig, use_container_width=True)

# Equity + holdings
st.subheader("Portfolio Breakdown")
col_left, col_right = st.columns(2)
with col_left:
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(x=equity.index, y=equity, name="Equity", line={"color": "#8b5cf6", "width": 2}))
    fig_eq.update_layout(title="Equity Curve", yaxis_title="USD", **DARK_LAYOUT)
    fig_eq.update_layout(height=350)
    st.plotly_chart(fig_eq, use_container_width=True)
with col_right:
    if "eth_holdings" in results:
        eth_h = results["eth_holdings"].dropna()
        fig_eth = go.Figure()
        fig_eth.add_trace(go.Scatter(x=eth_h.index, y=eth_h, name="ETH Holdings", line={"color": "#3b82f6", "width": 2}))
        fig_eth.update_layout(title="ETH Holdings Over Time", yaxis_title="ETH", **DARK_LAYOUT)
        fig_eth.update_layout(height=350)
        st.plotly_chart(fig_eth, use_container_width=True)

# Cash balance
st.subheader("Cash Balance Over Time")
if "cash" in results:
    cash = results["cash"].dropna()
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Scatter(x=cash.index, y=cash, name="Cash", line={"color": "#f59e0b", "width": 1.5}))
    fig_cash.update_layout(title="Cash Position", yaxis_title="USD", **DARK_LAYOUT)
    fig_cash.update_layout(height=300)
    st.plotly_chart(fig_cash, use_container_width=True)

# Monthly returns heatmap
st.divider()
st.subheader("Monthly Returns Heatmap")
monthly = (1 + returns).resample("ME").prod() - 1
if len(monthly) > 0:
    monthly_df = monthly.to_frame("ret")
    monthly_df["year"] = monthly_df.index.year
    monthly_df["month"] = monthly_df.index.month
    pivot = monthly_df.pivot_table(index="year", columns="month", values="ret", aggfunc="first")

    import plotly.express as px
    fig_heat = px.imshow(
        pivot * 100,
        title="Monthly Returns (%)",
        color_continuous_scale=["#ff3860", "#15151a", "#00d68f"],
        labels={"x": "Month", "y": "Year", "color": "Return %"},
        aspect="auto",
    )
    fig_heat.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=350)
    st.plotly_chart(fig_heat, use_container_width=True)

# Position changes (detect buy/sell events)
st.divider()
st.subheader("Detected Position Changes")
if "eth_holdings" in results:
    eth_h = results["eth_holdings"].dropna()
    changes = eth_h.diff().fillna(0)
    buys = changes[changes > 0.0001]
    sells = changes[changes < -0.0001]

    col_a, col_b = st.columns(2)
    col_a.metric("Detected Buys", f"{len(buys)}")
    col_b.metric("Detected Sells", f"{len(sells)}")

    if len(buys) > 0:
        buy_df = pd.DataFrame({"Date": buys.index, "ETH Added": buys.values, "Price": [float(eth["close"].reindex(buys.index).ffill().iloc[i]) for i in range(len(buys))]})
        buy_df["USD Spent"] = buy_df["ETH Added"] * buy_df["Price"]
        st.subheader("Buy Transactions")
        st.dataframe(buy_df, use_container_width=True, hide_index=True)