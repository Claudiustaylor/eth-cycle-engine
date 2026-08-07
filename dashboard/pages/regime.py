from __future__ import annotations

import streamlit as st

from data.storage import load_parquet

st.title("Current Regime")
df = load_parquet("latest_results")
if df is None or "regime" not in df:
    st.info("No regime results found. Run `python example_backtest.py` first.")
else:
    st.metric("Latest Regime", str(df["regime"].iloc[-1]))
