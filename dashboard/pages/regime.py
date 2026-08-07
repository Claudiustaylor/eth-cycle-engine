"""Current regime — regime classification, distribution, timeline."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    REGIME_COLORS,
    regime_distribution_chart,
    regime_timeline_chart,
)
from dashboard.data_loader import get_eth_data, get_results

st.set_page_config(page_title="Regime — ETH Cycle Engine", layout="wide", page_icon="🎯")

st.title("🎯 Current Regime")

results = get_results()
eth = get_eth_data()

if results is None or "regime" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

regimes = results["regime"].dropna()
latest_regime = str(regimes.iloc[-1])
latest_color = REGIME_COLORS.get(latest_regime, "#6b7280")

# Big metric
col1, col2, col3 = st.columns(3)
col1.metric("Current Regime", latest_regime.upper())
regime_counts = regimes.value_counts()
pct_in_regime = regime_counts.get(latest_regime, 0) / len(regimes) * 100
col2.metric("Days in This Regime", f"{regime_counts.get(latest_regime, 0)}", f"{pct_in_regime:.1f}% of history")
days_in_current = 0
for r in regimes.iloc[::-1]:
    if r == latest_regime:
        days_in_current += 1
    else:
        break
col3.metric("Current Streak", f"{days_in_current} days")

st.divider()

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(regime_distribution_chart(regimes), use_container_width=True)
with col_right:
    st.plotly_chart(regime_timeline_chart(regimes), use_container_width=True)

# Regime transition matrix
st.subheader("Regime Transition Matrix (probability of next regime)")
regime_list = list(REGIME_COLORS.keys())
transitions = {}
for i in range(len(regimes) - 1):
    curr = regimes.iloc[i]
    nxt = regimes.iloc[i + 1]
    if curr not in transitions:
        transitions[curr] = {}
    transitions[curr][nxt] = transitions[curr].get(nxt, 0) + 1

trans_matrix = []
for from_regime in regime_list:
    row = []
    total = sum(transitions.get(from_regime, {}).values())
    for to_regime in regime_list:
        count = transitions.get(from_regime, {}).get(to_regime, 0)
        row.append(count / total * 100 if total > 0 else 0)
    trans_matrix.append(row)

trans_df = pd.DataFrame(trans_matrix, index=regime_list, columns=regime_list)
st.dataframe(trans_df.round(1), use_container_width=True)