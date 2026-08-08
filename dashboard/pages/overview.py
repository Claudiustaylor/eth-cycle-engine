"""Market overview — ETH price, volume, key stats, latest regime."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import price_chart_with_signals, rolling_volatility_chart
from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="ETH Cycle Engine", layout="wide", page_icon="📊")

st.title("📊 Market Overview")
st.markdown("*See Ethereum's price history, current state, and key statistics at a glance.*")

eth = get_eth_data()
results = get_results()

if eth is None:
    st.error("Failed to load ETH data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

# ── Key metrics row ──
st.markdown("### Quick Stats")
latest_price = float(eth["close"].iloc[-1])
first_price = float(eth["close"].iloc[0])
total_ret = (latest_price / first_price - 1) * 100
max_price = float(eth["close"].max())
dd_from_ath = (latest_price / max_price - 1) * 100

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Current ETH Price", f"${latest_price:,.2f}")
col2.metric("Return Since Start", f"{total_ret:+.1f}%", help="Total price change from the first day in our dataset to now.")
col3.metric("All-Time High", f"${max_price:,.2f}", help="The highest ETH price ever recorded in our dataset.")
col4.metric("Drop from ATH", f"{dd_from_ath:.1f}%", help="How far the current price is below the all-time high. A -50% means ETH is half its peak price.")
col5.metric("Days of Data", f"{len(eth):,}", help="Total number of daily price records we have for ETH.")

with st.expander("📖 What am I looking at?"):
    st.markdown("""
    This is your dashboard home. It shows Ethereum's price over time with key statistics.

    - **Price Chart**: ETH's daily closing price with colored regime shading (see the Regime page for what each color means)
    - **Volatility**: How much the price swings. Higher = more risk but also more opportunity
    - **Returns Distribution**: A histogram showing how often ETH has big up-days vs down-days
    - **Volume**: How much ETH was traded each day — spikes often happen at market turning points
    """)

st.divider()

# ── Price chart ──
st.markdown("### ETH Price History")
if results is not None and "regime" in results:
    regimes = results["regime"].dropna()
    st.plotly_chart(price_chart_with_signals(eth, regimes=regimes), use_container_width=True)
    st.caption("💡 The colored background shading shows which market regime each day falls into. Blue = accumulation (potential buying zone), Green = bull market, Red = bear/capitulation. See the Regime page for details.")
else:
    st.plotly_chart(price_chart_with_signals(eth), use_container_width=True)

# ── Volatility and returns ──
st.markdown("### Volatility & Returns")
st.caption("Volatility measures how much the price swings. High volatility = bigger risk AND bigger opportunity.")

daily_returns = eth["close"].pct_change().dropna()

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(rolling_volatility_chart(daily_returns, 21), use_container_width=True)
with col_right:
    st.subheader("Daily Return Distribution")
    st.caption("This shows how often ETH has small daily moves (center) vs big moves (edges). The fat tails on the edges show that extreme days happen more often than a normal bell curve would predict — this is crypto.")
    fig = px.histogram(daily_returns * 100, nbins=100, title="Daily Returns (%)", labels={"value": "Return %"})
    fig.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"})
    st.plotly_chart(fig, use_container_width=True)

# ── Volume ──
st.markdown("### Trading Volume")
st.caption("Volume shows how much ETH changed hands each day. Spikes in volume often happen at market bottoms (panic selling) or tops (euphoric buying).")
fig_vol = go.Figure(go.Bar(x=eth.index, y=eth["volume"], name="Volume", marker_color="#3b82f6"))
fig_vol.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=250, margin={"l": 10, "r": 10, "t": 30, "b": 10})
st.plotly_chart(fig_vol, use_container_width=True)