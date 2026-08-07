"""Signal score — confidence, sub-scores, explainability."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from dashboard.components.charts import signal_confidence_chart
from data.storage import load_parquet

st.set_page_config(page_title="Signals — ETH Cycle Engine", layout="wide", page_icon="📡")

st.title("📡 Signal Score")

results = load_parquet("latest_results")

if results is None or "signal_score" not in results:
    st.warning("No signal results found. Run `python example_backtest.py` first.")
    st.stop()

scores = results["signal_score"].dropna()
latest_score = float(scores.iloc[-1])

# Determine band
if latest_score <= 20:
    band, action = "Strong Sell", "Extreme caution"
    color = "#ff3860"
elif latest_score <= 40:
    band, action = "Reduce", "Reduce exposure"
    color = "#ff3860"
elif latest_score <= 59:
    band, action = "Neutral", "Neutral"
    color = "#6b7280"
elif latest_score <= 74:
    band, action = "Accumulate", "Initial accumulation"
    color = "#00d68f"
elif latest_score <= 89:
    band, action = "Strong Accumulate", "Strong accumulation"
    color = "#00d68f"
else:
    band, action = "Extreme Accumulate", "Extreme accumulation opportunity"
    color = "#00d68f"

col1, col2, col3 = st.columns(3)
col1.metric("Latest Score", f"{latest_score:.0f}/100")
col2.metric("Signal Band", band)
col3.metric("Recommended Action", action)

st.divider()

st.plotly_chart(signal_confidence_chart(scores), use_container_width=True)

# Score distribution
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("Score Distribution")
    import plotly.express as px
    fig = px.histogram(scores, nbins=50, title="Signal Score Distribution", labels={"value": "Score"})
    fig.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=300, margin={"l": 10, "r": 10, "t": 30, "b": 10})
    st.plotly_chart(fig, use_container_width=True)
with col_right:
    st.subheader("Score Statistics")
    st.metric("Mean Score", f"{scores.mean():.1f}")
    st.metric("Median Score", f"{scores.median():.1f}")
    st.metric("Std Dev", f"{scores.std():.1f}")
    st.metric("Time in Accumulate Zone (>60)", f"{(scores > 60).mean() * 100:.1f}%")
    st.metric("Time in Sell Zone (<40)", f"{(scores < 40).mean() * 100:.1f}%")

# Latest signal explanation
st.divider()
st.subheader("Latest Signal Explanation")

report_path = Path("output/report.json")
if report_path.exists():
    report = json.loads(report_path.read_text())
    latest_signal = report.get("latest_signal", "")
    st.code(latest_signal, language="text")
else:
    st.info("Run `python example_backtest.py` to generate the latest signal explanation.")