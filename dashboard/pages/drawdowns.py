from __future__ import annotations

import streamlit as st

from dashboard.components.charts import drawdown_chart
from data.storage import load_parquet

st.title("Drawdown Analysis")
df = load_parquet("latest_results")
if df is None or "equity" not in df:
    st.info("No backtest results found. Run `python example_backtest.py` first.")
else:
    st.plotly_chart(drawdown_chart(df["equity"]), use_container_width=True)
