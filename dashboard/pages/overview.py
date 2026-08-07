"""Market overview — ETH price, volume, key stats, latest regime."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import price_chart_with_signals, rolling_volatility_chart
from data.storage import load_parquet

st.set_page_config(page_title="ETH Cycle Engine", layout="wide", page_icon="📊")

st.title("📊 Market Overview")

eth = load_parquet("eth_ohlcv_1d")
results = load_parquet("latest_results")

if eth is None:
    st.warning("No data found. Run `python example_backtest.py` first to download data and generate results.")
    st.code("cd /Users/ct/eth-cycle-engine && source .venv/bin/activate && python example_backtest.py")
    st.stop()

# Key metrics row
col1, col2, col3, col4, col5 = st.columns(5)
latest_price = float(eth["close"].iloc[-1])
first_price = float(eth["close"].iloc[0])
total_ret = (latest_price / first_price - 1) * 100
max_price = float(eth["close"].max())
dd_from_ath = (latest_price / max_price - 1) * 100

col1.metric("Latest ETH Price", f"${latest_price:,.2f}")
col2.metric("All-Time Return", f"{total_ret:+.1f}%")
col3.metric("ATH", f"${max_price:,.2f}")
col4.metric("Drawdown from ATH", f"{dd_from_ath:.1f}%")
col5.metric("Data Points", f"{len(eth):,}")

st.divider()

# Price chart
if results is not None and "regime" in results:
    regimes = results["regime"].dropna()
    st.plotly_chart(price_chart_with_signals(eth, regimes=regimes), use_container_width=True)
else:
    st.plotly_chart(price_chart_with_signals(eth), use_container_width=True)

# Returns and volatility
col_left, col_right = st.columns(2)
with col_left:
    daily_returns = eth["close"].pct_change().dropna()
    st.plotly_chart(rolling_volatility_chart(daily_returns, 21), use_container_width=True)
with col_right:
    st.subheader("Daily Return Distribution")
    import plotly.express as px
    fig = px.histogram(daily_returns * 100, nbins=100, title="Daily Returns (%)", labels={"value": "Return %"})
    fig.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"})
    st.plotly_chart(fig, use_container_width=True)

# Volume
st.subheader("Trading Volume")
import plotly.graph_objects as go

fig_vol = go.Figure(go.Bar(x=eth.index, y=eth["volume"], name="Volume", marker_color="#3b82f6"))
fig_vol.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=250, margin={"l": 10, "r": 10, "t": 30, "b": 10})
st.plotly_chart(fig_vol, use_container_width=True)