"""Drawdown analysis — how bad did it get and how long to recover?"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard.components.charts import drawdown_chart
from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="Drawdowns — ETH Cycle Engine", layout="wide", page_icon="📉")

st.title("📉 Drawdown Analysis")
st.markdown("*How much did the portfolio fall from its peak, and how long did it take to recover?*")

results = get_results()
eth = get_eth_data()

if results is None or "equity" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

equity = results["equity"].dropna()
dd = equity / equity.cummax() - 1

# ── Explanation ──
with st.expander("📖 What is a drawdown?"):
    st.markdown("""
    A **drawdown** is how far your portfolio has fallen from its highest point. It's the most important risk metric because it measures real pain.

    **Example:** If your portfolio peaked at $100,000 and then fell to $40,000, your drawdown is -60%. You've lost 60% of your money from the peak.

    **Why it matters:**
    - A -50% drawdown requires a +100% gain just to break even
    - A -90% drawdown requires a +900% gain to recover
    - Most investors panic and sell during deep drawdowns — this is where discipline matters most

    **Key questions this page answers:**
    - How bad did it get? (Max Drawdown)
    - How often was the portfolio underwater? (% time below peak)
    - How long did it take to recover?
    """)

# ── Key metrics ──
st.markdown("### The Pain Stats")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Max Drawdown", f"{dd.min() * 100:.1f}%", help="The worst peak-to-trough decline. This is the most you would have lost from a peak.")
current_dd = dd.iloc[-1] * 100
col2.metric("Current Drawdown", f"{current_dd:.1f}%", help="How far below peak the portfolio is right now.")
col3.metric("Average Drawdown", f"{dd.mean() * 100:.1f}%", help="On an average day, how far below peak was the portfolio?")
underwater_pct = (dd < 0).mean() * 100
col4.metric("Time Underwater", f"{underwater_pct:.1f}%", help="Percentage of days the portfolio was below its previous peak. High = lots of time waiting to recover.")

st.divider()

# ── Drawdown chart ──
st.markdown("### Strategy Drawdown Over Time")
st.caption("The red area shows how far below its peak the portfolio was at each point. Wider/deeper red = more pain. The question is: could you have held through this without panic-selling?")
col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(drawdown_chart(equity), use_container_width=True)
with col_right:
    st.subheader("Drawdown Distribution")
    st.caption("How often was the portfolio in shallow vs deep drawdown?")
    fig = px.histogram(dd[dd < 0] * 100, nbins=50, title="Drawdown Depth Frequency", labels={"value": "Drawdown %"})
    fig.update_layout(paper_bgcolor="#0a0a0b", plot_bgcolor="#15151a", font={"color": "#e0e0e8"}, height=350, margin={"l": 10, "r": 10, "t": 30, "b": 10})
    st.plotly_chart(fig, use_container_width=True)

# ── ETH comparison ──
if eth is not None:
    st.markdown("### ETH Buy & Hold Drawdown (for comparison)")
    st.caption("This shows the drawdown if you simply bought ETH and held — no strategy, no selling. Compare this to the strategy's drawdown above. A good strategy should have a smaller drawdown than buy-and-hold.")
    eth_dd = eth["close"] / eth["close"].cummax() - 1
    col1b, col2b, col3b = st.columns(3)
    col1b.metric("ETH Max DD", f"{eth_dd.min() * 100:.1f}%", help="The worst drawdown for buy-and-hold ETH.")
    col2b.metric("ETH Current DD", f"{eth_dd.iloc[-1] * 100:.1f}%")
    col3b.metric("ETH Time Underwater", f"{(eth_dd < 0).mean() * 100:.1f}%")
    st.plotly_chart(drawdown_chart(eth["close"]), use_container_width=True)

# ── Drawdown episodes ──
st.divider()
st.markdown("### Top Drawdown Episodes")
st.caption("Major drawdown events: when did the portfolio peak, how deep did it fall, and how long did recovery take?")

import pandas as pd

dd_episodes = []
in_dd = False
trough_idx = None
peak_idx = equity.idxmax()
peak_val = equity.iloc[0]

for i in range(len(equity)):
    val = equity.iloc[i]
    idx = equity.index[i]
    if val >= peak_val:
        if in_dd:
            dd_episodes.append({
                "Peak Date": str(pd.Timestamp(peak_idx).date()),
                "Trough Date": str(pd.Timestamp(trough_idx).date()) if trough_idx else "",
                "Recovery Date": str(pd.Timestamp(idx).date()),
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
    st.dataframe(pd.DataFrame(dd_episodes).head(5), use_container_width=True, hide_index=True)
else:
    st.info("No complete drawdown-recovery episodes found in this dataset.")