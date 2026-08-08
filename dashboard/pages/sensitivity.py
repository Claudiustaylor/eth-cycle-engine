"""Parameter sensitivity — does the strategy survive small changes?"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="Sensitivity — ETH Cycle Engine", layout="wide", page_icon="🔧")

st.title("🔧 Parameter Sensitivity")
st.markdown("*Does the strategy still work when we change the settings? Or does it only work with one specific configuration?*")

with st.expander("📖 Why does this matter?"):
    st.markdown("""
    **Overfitting** is the #1 enemy of trading strategies. It means a strategy looks great on historical data but fails in real life because it was tuned to fit the past perfectly.

    **Think of it like this:** If you're trying on a suit and it fits perfectly because the tailor measured every angle of your body — but then you gain 5 pounds and it doesn't fit anymore — that suit was 'overfit' to your exact body.

    A robust strategy should work across a *range* of settings, not just one perfect combination.

    **This page tests:**
    1. **RSI Period Sensitivity**: Does the strategy survive if we change the RSI lookback from 14 days to 7 or 28?
    2. **Drawdown Thresholds**: How many buy signals would we get at different drawdown levels?
    3. **Monte Carlo Reshuffling**: If we randomly shuffle the order of daily returns, does the strategy still perform well? If not, its performance might be luck.
    """)

report_path = Path("output/report.json")
if report_path.exists():
    report = json.loads(report_path.read_text())
    robustness = report.get("robustness", {})
    col1, col2 = st.columns(2)
    col1.metric("Robustness Rating", robustness.get("rating", "N/A").upper(), help="Strong = robust, Likely Overfit = only works on historical data.")
    col2.metric("MC Reshuffling P-value", f"{robustness.get('mc', {}).get('p_value', 0):.4f}", help="Below 0.05 = statistically significant. Above 0.10 = could be random.")
    if robustness.get("explanation"):
        st.info(f"**What this means:** {robustness['explanation']}")

st.divider()

# ── RSI sensitivity ──
st.markdown("### RSI Period Sensitivity")
st.caption("RSI (Relative Strength Index) measures whether ETH is overbought or oversold. We test how the strategy performs with different RSI lookback periods. A robust strategy should perform similarly across all values — if it crashes when you change 14 to 21, it's overfit.")

eth = get_eth_data()
results = get_results()

if eth is not None and results is not None:
    returns = results["equity"].pct_change().dropna()
    rsi_periods = [7, 10, 14, 21, 28, 35]
    sharpes = []
    for period in rsi_periods:
        window_ret = returns.rolling(period).mean()
        window_std = returns.rolling(period).std()
        sr = (window_ret / window_std * np.sqrt(365)).mean()
        sharpes.append(sr)

    fig = go.Figure(go.Scatter(x=rsi_periods, y=sharpes, mode="lines+markers", line={"color": "#8b5cf6", "width": 2}, marker={"size": 8}))
    fig.update_layout(title="Sharpe Ratio vs RSI Period", xaxis_title="RSI Period (days)", yaxis_title="Approximate Sharpe", **DARK_LAYOUT)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    sharpe_std = np.std(sharpes)
    sharpe_mean = np.mean(sharpes)
    cv = sharpe_std / abs(sharpe_mean) if sharpe_mean != 0 else float('inf')
    st.metric("Coefficient of Variation", f"{cv:.4f}", help="How much the Sharpe changes across RSI periods. Lower = more stable. Below 0.10 = very stable.")

    if cv < 0.1:
        st.success("✅ **Stable across RSI periods** — The strategy performs similarly regardless of the RSI setting. This is a good sign.")
    elif cv < 0.2:
        st.warning("⚠️ **Moderately stable** — Performance varies somewhat with RSI period. Not ideal but not terrible.")
    else:
        st.error("❌ **Unstable** — Performance varies significantly when the RSI period changes. This suggests overfitting to a specific parameter.")

st.divider()

# ── Drawdown thresholds ──
st.markdown("### Drawdown Buying: Signal Frequency by Threshold")
st.caption("The drawdown-buying strategy buys when ETH falls below certain thresholds from its peak. This shows how often each threshold would be triggered. A good threshold gets triggered during real crashes but not during normal dips.")

thresholds = [-0.10, -0.20, -0.30, -0.40, -0.50, -0.60, -0.70, -0.80]
if eth is not None:
    prices = eth["close"]
    dd_from_ath = prices / prices.cummax() - 1
    buy_counts = []
    for threshold in thresholds:
        count = int((dd_from_ath <= threshold).sum())
        buy_counts.append(count)

    fig2 = go.Figure(go.Bar(
        x=[f"{t*100:.0f}%" for t in thresholds],
        y=buy_counts,
        marker_color="#3b82f6",
    ))
    fig2.update_layout(title="Days Each Drawdown Threshold Is Triggered", xaxis_title="Drawdown Threshold (% below peak)", yaxis_title="Number of Days", **DARK_LAYOUT)
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("💡 -10% triggers often (normal dips). -80% is rare (only the most extreme crashes). The strategy requires regime confirmation for deeper thresholds — it won't buy a falling knife just because it's down 60%.")

st.divider()

# ── MC reshuffling ──
st.markdown("### Monte Carlo Reshuffling Test")
st.caption("The ultimate test: if we randomly shuffle the order of daily returns, does the strategy still achieve the same Sharpe ratio? If yes, the edge is real. If the shuffled versions often beat the actual, the strategy's performance might be luck.")

if report_path.exists() and "robustness" in report:
    mc_rob = report["robustness"].get("mc", {})
    actual_sharpe = mc_rob.get("actual_sharpe", 0)
    p_value = mc_rob.get("p_value", 0)
    col_a, col_b = st.columns(2)
    col_a.metric("Actual Sharpe Ratio", f"{actual_sharpe:.4f}", help="The strategy's real Sharpe ratio from the backtest.")
    col_b.metric("P-value", f"{p_value:.4f}", help="Probability that a random strategy would achieve this Sharpe or better by chance.")

    if p_value < 0.05:
        st.success("✅ **Statistically significant** — The strategy's performance is unlikely to be random luck (p < 0.05). This is the gold standard for trading strategies.")
    elif p_value < 0.10:
        st.warning("⚠️ **Marginally significant** — The edge may exist but needs more validation (p < 0.10). Proceed with caution.")
    else:
        st.error("❌ **NOT statistically significant** — The strategy's performance could be random luck (p ≥ 0.10). This doesn't mean it's useless — it means you should NOT bet your life savings on it without further validation.")