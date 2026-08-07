from __future__ import annotations

import streamlit as st

from dashboard.components.charts import price_chart_with_signals
from data.storage import load_parquet

st.title("Market Overview")
df = load_parquet("eth_ohlcv_1d")
if df is None:
    st.info("No cached data found. Run `python example_backtest.py` first.")
else:
    st.plotly_chart(price_chart_with_signals(df), use_container_width=True)
