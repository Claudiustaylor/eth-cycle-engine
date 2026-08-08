"""Trade history — what did the strategy actually do?"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from dashboard.components.style import inject_luxury_css

inject_luxury_css()

from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="Trade History — ETH Cycle Engine", layout="wide", page_icon="📋")

st.title("📋 Trade History")
st.markdown("*See exactly what the strategy did — every day's return, position changes, and monthly performance.*")

results = get_results()
eth = get_eth_data()

if results is None or "equity" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

equity = results["equity"].dropna()
returns = equity.pct_change().dropna()

# ── Explanation ──
with st.expander("📖 What am I looking at?"):
    st.markdown("""
    This page shows the day-by-day activity of the strategy:

    - **Daily Returns**: Each day's gain or loss. Green = up, red = down. The pattern tells you if the strategy is consistent or erratic.
    - **Equity Curve**: Your total portfolio value over time.
    - **ETH Holdings**: How much ETH you're holding at each point. Watch for the strategy accumulating during dips and trimming during rallies.
    - **Cash Position**: How much cash you're keeping on the sidelines. A good strategy holds cash during overbought periods and deploys during opportunities.
    - **Monthly Returns Heatmap**: A calendar view showing which months were good (green) vs bad (red). Look for patterns — does the strategy lose money in the same months every year?
    - **Buy Transactions**: Every time the strategy decided to buy ETH, with the amount and price.
    """)

# ── Summary stats ──
st.markdown("### Quick Stats")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Days Analyzed", f"{len(equity):,}")
positive_days = (returns > 0).sum()
col2.metric("Green Days (Up)", f"{positive_days} ({positive_days / len(returns) * 100:.1f}%)", help="Days the portfolio made money.")
negative_days = (returns < 0).sum()
col3.metric("Red Days (Down)", f"{negative_days} ({negative_days / len(returns) * 100:.1f}%)", help="Days the portfolio lost money.")
best_day = returns.max() * 100
col4.metric("Best Single Day", f"+{best_day:.1f}%", help="The biggest single-day gain.")

st.divider()

# ── Daily returns ──
st.markdown("### Daily Returns")
st.caption("Each bar is one day. Green = portfolio went up, Red = portfolio went down. Taller bars = bigger moves. Look for patterns: are big red days clustered (crash periods) or scattered (normal volatility)?")

fig = go.Figure()
colors = ["#22c55e" if r > 0 else "#ef4444" for r in returns]
fig.add_trace(go.Bar(x=returns.index, y=returns * 100, marker_color=colors, name="Daily Return %"))
fig.update_layout(title="Daily Strategy Returns (%)", yaxis_title="Return %", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
fig.update_layout(height=350)
st.plotly_chart(fig, use_container_width=True)

# ── Equity, ETH, Cash ──
st.markdown("### Portfolio Breakdown")
st.caption("How your portfolio was split between cash and ETH over time. A good strategy shifts to cash before crashes and deploys cash during opportunities.")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("#### Portfolio Value")
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(x=equity.index, y=equity, name="Portfolio Value", line={"color": "#e63946", "width": 2}))
    fig_eq.update_layout(title="Total Portfolio Value ($)", yaxis_title="USD", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
    fig_eq.update_layout(height=350)
    st.plotly_chart(fig_eq, use_container_width=True)
with col_right:
    if "eth_holdings" in results:
        eth_h = results["eth_holdings"].dropna()
        st.markdown("#### ETH Holdings")
        fig_eth = go.Figure()
        fig_eth.add_trace(go.Scatter(x=eth_h.index, y=eth_h, name="ETH Holdings", line={"color": "#e63946", "width": 2}))
        fig_eth.update_layout(title="ETH Units Held", yaxis_title="ETH", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
        fig_eth.update_layout(height=350)
        st.plotly_chart(fig_eth, use_container_width=True)

# ── Cash ──
if "cash" in results:
    cash = results["cash"].dropna()
    st.markdown("#### Cash Position")
    st.caption("How much cash you're holding. High cash = the strategy is cautious. Low cash = the strategy is fully invested.")
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Scatter(x=cash.index, y=cash, name="Cash", line={"color": "#f59e0b", "width": 1.5}))
    fig_cash.update_layout(title="Cash Balance ($)", yaxis_title="USD", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
    fig_cash.update_layout(height=300)
    st.plotly_chart(fig_cash, use_container_width=True)

# ── Monthly heatmap ──
st.divider()
st.markdown("### Monthly Returns Heatmap")
st.caption("Each cell is a month. Green = profitable month, Red = losing month. Darker = bigger move. Look for patterns: are certain months consistently good or bad?")

monthly = (1 + returns).resample("ME").prod() - 1
if len(monthly) > 0:
    monthly_df = monthly.to_frame("ret")
    monthly_df["year"] = monthly_df.index.year
    monthly_df["month"] = monthly_df.index.month
    pivot = monthly_df.pivot_table(index="year", columns="month", values="ret", aggfunc="first")

    fig_heat = px.imshow(
        pivot * 100,
        title="Monthly Returns (%) — Green = Profit, Red = Loss",
        color_continuous_scale=["#ef4444", "#121212", "#22c55e"],
        labels={"x": "Month", "y": "Year", "color": "Return %"},
        aspect="auto",
    )
    fig_heat.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#121212", font={"color": "#f5f5f5"}, height=350)
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("💡 Look for rows (years) where most months are green — those were good years. Rows with lots of red = bad years. A consistent pattern across years suggests the strategy has a real, repeatable edge.")

# ── Buy transactions ──
st.divider()
st.markdown("### Detected Position Changes")
st.caption("Every time the strategy changed its ETH position. Buys = the strategy found a buying opportunity. Sells = the strategy reduced exposure.")

if "eth_holdings" in results:
    eth_h = results["eth_holdings"].dropna()
    changes = eth_h.diff().fillna(0)
    buys = changes[changes > 0.0001]
    sells = changes[changes < -0.0001]

    col_a, col_b = st.columns(2)
    col_a.metric("Detected Buys", f"{len(buys)}", help="Number of times the strategy added to its ETH position.")
    col_b.metric("Detected Sells", f"{len(sells)}", help="Number of times the strategy reduced its ETH position.")

    if len(buys) > 0:
        buy_df = pd.DataFrame({
            "Date": [str(d.date()) for d in buys.index],
            "ETH Added": buys.values,
            "Price": [float(eth["close"].reindex(buys.index).ffill().iloc[i]) for i in range(len(buys))],
        })
        buy_df["USD Spent"] = buy_df["ETH Added"] * buy_df["Price"]
        st.markdown("#### Buy Transactions")
        st.dataframe(buy_df, use_container_width=True, hide_index=True)
        st.caption("💡 Look at the prices — did the strategy buy when ETH was cheap (low price = good buy) or expensive? A good strategy buys low.")