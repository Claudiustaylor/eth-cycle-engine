"""Historical backtest — how would the strategy have performed?"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
from pathlib import Path

import streamlit as st

from dashboard.components.charts import (
    drawdown_chart,
    equity_curve_chart,
    exposure_chart,
    rolling_sharpe_chart,
    rolling_volatility_chart,
)
from dashboard.components.style import inject_luxury_css

inject_luxury_css()

from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="Backtest — ETH Cycle Engine", layout="wide", page_icon="📜")

st.title("📜 Historical Backtest")
st.markdown("*If you had followed this strategy starting with $50,000, here's what would have happened.*")

results = get_results()
eth = get_eth_data()

if results is None or "equity" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

equity = results["equity"].dropna()
cash = results["cash"].dropna()
eth_holdings = results["eth_holdings"].dropna()
returns = equity.pct_change().dropna()

# ── Explanation ──
with st.expander("📖 What is a backtest?"):
    st.markdown("""
    A **backtest** simulates what would have happened if you followed the strategy from start to finish.

    Starting with $50,000, the system:
    1. Looks at each day's data (without seeing the future — no cheating)
    2. Computes the signal score
    3. Decides whether to buy, sell, or hold based on that score
    4. Applies realistic trading costs (fees, spread, slippage)
    5. Tracks your portfolio value over time

    **Important caveats:**
    - Past performance does NOT guarantee future results
    - The backtest can't capture real-world issues like order rejections, exchange outages, or your own emotions
    - We use walk-forward validation (separate page) to check if the strategy actually works or just got lucky
    """)

# ── Key metrics ──
st.markdown("### Bottom Line")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Final Value", f"${equity.iloc[-1]:,.0f}", help="Your portfolio's final value in USD.")
col2.metric("Total Return", f"{(equity.iloc[-1] / equity.iloc[0] - 1) * 100:.1f}%", help="Total growth from start to finish.")
col3.metric("Max Drawdown", f"{(equity / equity.cummax() - 1).min() * 100:.1f}%", help="The worst peak-to-trough decline. A -90% max DD means at one point, your portfolio lost 90% of its value. This is the 'how much pain' metric.")
ann_vol = returns.std() * (365**0.5) * 100
col4.metric("Annualized Vol", f"{ann_vol:.1f}%", help="How much your portfolio value swings. Stock market is ~15-20%. Crypto is typically 50-80%.")
sharpe = returns.mean() / returns.std() * (365**0.5) if returns.std() > 0 else 0
col5.metric("Sharpe Ratio", f"{sharpe:.3f}", help="Risk-adjusted return. Above 1.0 is good, above 2.0 is excellent. Measures return per unit of risk.")
years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1)
cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
col6.metric("CAGR", f"{cagr * 100:.1f}%", help="Compound Annual Growth Rate — the average yearly return if it grew at a steady rate.")

st.divider()

# ── Equity curve ──
st.markdown("### Portfolio Value Over Time")
st.caption("The purple line is your strategy. The gray dashed line is what you'd have if you just bought ETH on day 1 and held. Compare them — which would you prefer?")

if eth is not None:
    bh_equity = (eth["close"] / eth["close"].iloc[0] * equity.iloc[0]).reindex(equity.index).ffill()
    st.plotly_chart(equity_curve_chart(equity, bh_equity, "Buy & Hold ETH"), use_container_width=True)
else:
    st.plotly_chart(equity_curve_chart(equity), use_container_width=True)

# ── Drawdown & exposure ──
st.markdown("### Risk & Allocation")
col_left, col_right = st.columns(2)
with col_left:
    st.markdown("#### Drawdown (Underwater Plot)")
    st.caption("This shows how far below its peak your portfolio was at each point. The deeper the red, the more painful it was. The question is: could you have held through this?")
    st.plotly_chart(drawdown_chart(equity), use_container_width=True)
with col_right:
    st.markdown("#### Cash vs ETH Allocation")
    st.caption("Blue = cash sitting on the sidelines. Purple = ETH you're holding. A good strategy moves to cash before crashes and deploys cash during opportunities.")
    eth_value = eth_holdings * eth["close"].reindex(equity.index).ffill() if eth is not None else equity - cash
    st.plotly_chart(exposure_chart(cash, eth_value), use_container_width=True)

# ── Rolling metrics ──
st.markdown("### Rolling Performance")
st.caption("These charts show how performance changed over time. If the strategy was only good during one specific period, that's a red flag for overfitting.")

col_left2, col_right2 = st.columns(2)
with col_left2:
    window = st.slider("Rolling window (days)", min_value=30, max_value=504, value=252, step=21, help="How many days to look back at a time. 252 = ~1 year.")
    st.caption("**Rolling Sharpe Ratio** — if this line stays above 0 consistently, the strategy has a real edge. If it swings wildly between +2 and -2, the strategy is unstable.")
    st.plotly_chart(rolling_sharpe_chart(returns, window), use_container_width=True)
with col_right2:
    vol_window = st.slider("Volatility window (days)", min_value=7, max_value=90, value=21, step=7)
    st.caption("**Rolling Volatility** — when this spikes, the market is in chaos. The strategy should ideally reduce risk during these periods.")
    st.plotly_chart(rolling_volatility_chart(returns, vol_window), use_container_width=True)

# ── Strategy stats from report ──
st.divider()
st.markdown("### Strategy Summary")

report_path = Path("output/report.json")
if report_path.exists():
    report = json.loads(report_path.read_text())
    strat = report.get("strategy", {})
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total Trades", f"{strat.get('num_trades', 0):.0f}", help="How many buy/sell actions the strategy took.")
    col_b.metric("Sortino Ratio", f"{strat.get('sortino_ratio', 0):.3f}", help="Like Sharpe but only penalizes downside swings. Better for crypto.")
    col_c.metric("Calmar Ratio", f"{strat.get('calmar_ratio', 0):.3f}", help="CAGR divided by max drawdown. Was the return worth the pain?")
    col_d.metric("Win Rate", f"{strat.get('win_rate', 0) * 100:.1f}%", help="% of trades that were profitable.")