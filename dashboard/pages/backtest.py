"""Historical backtest — equity curve, drawdown, rolling metrics, trade log."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import (
    drawdown_chart,
    equity_curve_chart,
    exposure_chart,
    rolling_sharpe_chart,
    rolling_volatility_chart,
)
from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="Backtest — ETH Cycle Engine", layout="wide", page_icon="📜")

st.title("📜 Historical Backtest")

results = get_results()
eth = get_eth_data()

if results is None or "equity" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

equity = results["equity"].dropna()
cash = results["cash"].dropna()
eth_holdings = results["eth_holdings"].dropna()
returns = equity.pct_change().dropna()

# Key metrics
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Final Value", f"${equity.iloc[-1]:,.0f}")
col2.metric("Total Return", f"{(equity.iloc[-1] / equity.iloc[0] - 1) * 100:.1f}%")
col3.metric("Max Drawdown", f"{(equity / equity.cummax() - 1).min() * 100:.1f}%")
ann_vol = returns.std() * (365 ** 0.5) * 100
col4.metric("Annualized Vol", f"{ann_vol:.1f}%")
sharpe = returns.mean() / returns.std() * (365 ** 0.5) if returns.std() > 0 else 0
col5.metric("Sharpe Ratio", f"{sharpe:.3f}")
years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1)
cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
col6.metric("CAGR", f"{cagr * 100:.1f}%")

st.divider()

# Equity curve with buy & hold benchmark
if eth is not None:
    bh_equity = (eth["close"] / eth["close"].iloc[0] * equity.iloc[0]).reindex(equity.index).ffill()
    st.plotly_chart(equity_curve_chart(equity, bh_equity, "Buy & Hold"), use_container_width=True)
else:
    st.plotly_chart(equity_curve_chart(equity), use_container_width=True)

# Drawdown and exposure
col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(drawdown_chart(equity), use_container_width=True)
with col_right:
    eth_value = eth_holdings * eth["close"].reindex(equity.index).ffill() if eth is not None else equity - cash
    st.plotly_chart(exposure_chart(cash, eth_value), use_container_width=True)

# Rolling metrics
col_left2, col_right2 = st.columns(2)
with col_left2:
    window = st.slider("Rolling window (days)", min_value=30, max_value=504, value=252, step=21)
    st.plotly_chart(rolling_sharpe_chart(returns, window), use_container_width=True)
with col_right2:
    vol_window = st.slider("Volatility window (days)", min_value=7, max_value=90, value=21, step=7)
    st.plotly_chart(rolling_volatility_chart(returns, vol_window), use_container_width=True)

# Trade log
st.divider()
st.subheader("Trade Log")

import json
from pathlib import Path

report_path = Path("output/report.json")
if report_path.exists():
    report = json.loads(report_path.read_text())
    strat = report.get("strategy", {})
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total Trades", f"{strat.get('num_trades', 0):.0f}")
    col_b.metric("Win Rate", f"{strat.get('win_rate', 0) * 100:.1f}%")
    col_c.metric("CAGR", f"{strat.get('cagr', 0) * 100:.1f}%")
    col_d.metric("Sortino", f"{strat.get('sortino_ratio', 0):.3f}")