from __future__ import annotations

import streamlit as st

from dashboard.components.charts import signal_confidence_chart
from data.storage import load_parquet

st.title("Signal Score")
df = load_parquet("latest_results")
if df is None or "signal_score" not in df:
    st.info("No signal results found. Run `python example_backtest.py` first.")
else:
    st.plotly_chart(signal_confidence_chart(df["signal_score"]), use_container_width=True)
