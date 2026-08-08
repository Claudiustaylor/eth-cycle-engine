"""Signal score — the system's buy/sell confidence level."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
from pathlib import Path

import plotly.express as px
import streamlit as st

from dashboard.components.charts import signal_confidence_chart
from dashboard.components.style import inject_luxury_css

inject_luxury_css()

from dashboard.data_loader import get_results

st.set_page_config(page_title="Signals — ETH Cycle Engine", layout="wide", page_icon="📡")

st.title("📡 Signal Score")
st.markdown("*The system's confidence level for buying or selling ETH right now.*")

results = get_results()

if results is None or "signal_score" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

scores = results["signal_score"].dropna()
latest_score = float(scores.iloc[-1])

# ── Explanation ──
with st.expander("📖 How does the signal score work?"):
    st.markdown("""
    The signal score is a **0-100 confidence level** that combines 8 different analyses into one number.

    **It is NOT a simple buy/sell signal.** It's a confidence meter:

    | Score | Label | What It Means |
    |-------|-------|-------------|
    | 0-20 | 🔴 Strong Sell | Multiple warning signs — reduce exposure |
    | 21-40 | 🟠 Reduce | Bearish signals building up |
    | 41-59 | ⚪ Neutral | No clear edge — hold and wait |
    | 60-74 | 🟡 Accumulate | Conditions becoming favorable — start buying small amounts |
    | 75-89 | 🟢 Strong Accumulate | Strong buying conditions — buy more |
    | 90-100 | 🟣 Extreme Accumulate | Rare opportunity — multiple signals aligned |

    **The 8 sub-scores that make up the total:**
    - **Valuation (20%)**: Is ETH cheap or expensive vs its history? Deep drawdowns = cheaper.
    - **Trend (15%)**: Are moving averages pointing up or down?
    - **Momentum (15%)**: Is RSI oversold (buying opportunity) or overbought?
    - **Volatility (10%)**: High volatility with contraction often signals panic → opportunity.
    - **Derivatives (10%)**: Funding rates & liquidations (needs paid data — currently neutral).
    - **On-Chain (10%)**: Exchange flows & MVRV (needs paid data — currently neutral).
    - **Macro (10%)**: Stock market trend, dollar strength, interest rates.
    - **Regime (10%)**: What market phase are we in?
    """)

# ── Current score ──
st.markdown("### Current Signal")

if latest_score <= 20:
    band, action, color = "Strong Sell", "Extreme caution — reduce exposure", "#ef4444"
elif latest_score <= 40:
    band, action, color = "Reduce", "Reduce exposure", "#ef4444"
elif latest_score <= 59:
    band, action, color = "Neutral", "Hold — no clear edge", "#666666"
elif latest_score <= 74:
    band, action, color = "Accumulate", "Start buying in small amounts", "#22c55e"
elif latest_score <= 89:
    band, action, color = "Strong Accumulate", "Buy more aggressively", "#22c55e"
else:
    band, action, color = "Extreme Accumulate", "Rare opportunity — deploy capital", "#22c55e"

col1, col2, col3 = st.columns(3)
col1.metric("Latest Score", f"{latest_score:.0f}/100", help="0 = extreme sell signal, 100 = extreme buy signal, 50 = neutral")
col2.metric("Signal Band", band)
col3.metric("Recommended Action", action)

# Progress bar visualization
st.markdown("#### Score Position")
st.progress(min(latest_score, 100) / 100, text=f"{latest_score:.0f}/100 — {band}")

st.divider()

# ── Score over time ──
st.markdown("### Signal Score Over Time")
st.caption("The colored bands show the confidence zones. Watch how the score moves between zones during bull and bear markets. A good strategy accumulates when the score is high (green zones) and trims when it's low (red zones).")
st.plotly_chart(signal_confidence_chart(scores), use_container_width=True)

# ── Score distribution ──
st.markdown("### Score Distribution")
st.caption("How often does the signal reach each zone? If the signal is almost always 'neutral,' the strategy isn't finding many opportunities. If it's frequently in 'extreme accumulate,' it may be too aggressive.")

col_left, col_right = st.columns(2)
with col_left:
    fig = px.histogram(scores, nbins=50, title="How Often Each Score Occurs", labels={"value": "Score"})
    fig.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#121212", font={"color": "#f5f5f5"}, height=300, margin={"l": 10, "r": 10, "t": 30, "b": 10})
    st.plotly_chart(fig, use_container_width=True)
with col_right:
    st.markdown("#### Statistics")
    st.metric("Average Score", f"{scores.mean():.1f}", help="If this is around 50, the system is balanced. Well above 50 = bias toward buying.")
    st.metric("Median Score", f"{scores.median():.1f}")
    st.metric("Std Deviation", f"{scores.std():.1f}", help="How much the score varies. High = the system adapts a lot. Low = it's fairly constant.")
    st.metric("Time in Buy Zone (>60)", f"{(scores > 60).mean() * 100:.1f}%", help="% of days the system said 'accumulate' or higher.")
    st.metric("Time in Sell Zone (<40)", f"{(scores < 40).mean() * 100:.1f}%", help="% of days the system said 'reduce' or lower.")

# ── Latest signal explanation ──
st.divider()
st.markdown("### Latest Signal Explanation")
st.caption("Every signal the system generates comes with a full breakdown of WHY it reached that score.")

report_path = Path("output/report.json")
if report_path.exists():
    report = json.loads(report_path.read_text())
    latest_signal = report.get("latest_signal", "")
    st.code(latest_signal, language="text")
    st.caption("💡 Each line references a specific data point. If derivatives or on-chain say 'neutral 50/100,' that means we don't have paid data for those — the system defaults to neutral instead of guessing.")
else:
    st.info("Signal explanation will appear here after data loads.")