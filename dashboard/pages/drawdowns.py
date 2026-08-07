"""Drawdown analysis — underwater plot, drawdown statistics, recovery times."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import drawdown_chart
from data.storage import load_parquet

st.set_page_config(page_title="Drawdowns — ETH Cycle Engine", layout="wide", page_icon="📉")

st.title("📉 Drawdown Analysis")

results = load_parquet("latest_results")
eth = load_parquet("eth_ohlcv_1d")

if results is None or "equity" not in results:
    st.warning("No backtest results found. Run `python example_backtest.py` first.")
    st.stop()

equity = results["equity"].dropna()
dd = equity / equity.cummax() - 1

# Key drawdown metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Max Drawdown", f"{dd.min() * 100:.1f}%")
# Current drawdown
current_dd = dd.iloc[-1] * 100
col2.metric("Current Drawdown", f"{current_dd:.1f}%")
# Average drawdown
col3.metric("Avg Drawdown", f"{dd.mean() * 100:.1f}%")
# Time underwater
underwater_pct = (dd < 0).mean() * 100
col4.metric("Time Underwater", f"{underwater_pct:.1f}%")

st.divider()

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(drawdown_chart(equity), use_container_width=True)
with col_right:
    # Drawdown histogram
    import plotly.express as px
    fig = px.histogram(dd[dd < 0] * 100, nbins=50, title="Drawdown Distribution", labels={"value": "DD %"})
    fig.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=350, margin={"l": 10, "r": 10, "t": 30, "b": 10})
    st.plotly_chart(fig, use_container_width=True)

# ETH price drawdown (buy & hold perspective)
if eth is not None:
    st.subheader("ETH Buy & Hold Drawdown (for comparison)")
    eth_dd = eth["close"] / eth["close"].cummax() - 1
    col1b, col2b, col3b = st.columns(3)
    col1b.metric("ETH Max DD", f"{eth_dd.min() * 100:.1f}%")
    col2b.metric("ETH Current DD", f"{eth_dd.iloc[-1] * 100:.1f}%")
    col3b.metric("ETH Time Underwater", f"{(eth_dd < 0).mean() * 100:.1f}%")
    st.plotly_chart(drawdown_chart(eth["close"]), use_container_width=True)

# Recovery analysis
st.subheader("Top 5 Drawdown Episodes")
dd_episodes = []
peak_idx = equity.idxmax()
in_dd = False
trough_idx = None
peak_val = equity.iloc[0]

for i in range(len(equity)):
    val = equity.iloc[i]
    idx = equity.index[i]
    if val >= peak_val:
        if in_dd:
            # Recovery
            dd_episodes.append({
                "Peak Date": str(peak_idx.date()) if hasattr(peak_idx, 'date') else str(peak_idx),
                "Trough Date": str(trough_idx.date()) if trough_idx and hasattr(trough_idx, 'date') else str(trough_idx),
                "Recovery Date": str(idx.date()) if hasattr(idx, 'date') else str(idx),
                "Max DD %": f"{(equity.loc[trough_idx] / peak_val - 1) * 100:.1f}%" if trough_idx else "",
                "Recovery Days": (idx - trough_idx).days if trough_idx else 0,
            })
            in_dd = False
        peak_val = val
        peak_idx = idx
    else:
        if not in_dd:
            in_dd = True
            trough_idx = idx
        if val < equity.loc[trough_idx]:
            trough_idx = idx

if dd_episodes:
    st.dataframe(pd.DataFrame(dd_episodes).head(5), use_container_width=True)
else:
    st.info("No complete drawdown-recovery episodes found.")