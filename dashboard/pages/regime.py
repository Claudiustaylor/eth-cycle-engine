"""Current regime — what phase of the market cycle are we in?"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    REGIME_COLORS,
    regime_distribution_chart,
    regime_timeline_chart,
)
from dashboard.data_loader import get_results

st.set_page_config(page_title="Regime — ETH Cycle Engine", layout="wide", page_icon="🎯")

st.title("🎯 Current Market Regime")
st.markdown("*What phase of the crypto market cycle are we in right now?*")

results = get_results()

if results is None or "regime" not in results:
    st.error("Failed to load data. The app will auto-download on first load — refresh if this persists.")
    st.stop()

regimes = results["regime"].dropna()
latest_regime = str(regimes.iloc[-1])

# ── What is a regime? ──
with st.expander("📖 What is a market regime?"):
    st.markdown("""
    Markets move in cycles. A **regime** is the current phase of that cycle — like the seasons of the year.

    Just as you'd dress differently in winter vs summer, you should invest differently in a **bull market** (prices rising) vs a **bear market** (prices falling).

    The system classifies each day into one of 10 regimes using technical indicators like moving averages, RSI, and drawdown depth. This helps you understand whether conditions favor buying, selling, or waiting.

    **The 10 regimes (simplified):**
    - 🔄 **Accumulation**: Price has crashed and stabilized — smart money is quietly buying
    - 🚀 **Early Bull**: Recovery beginning, trend turning up
    - 📈 **Bull Expansion**: Full uptrend, biggest gains happen here
    - ⚠️ **Late Bull**: Rising but exhausted — start planning exits
    - 🚀 **Blow-Off**: Parabolic spike — often marks the top, very dangerous
    - 📤 **Distribution**: Topping process — smart money selling to late buyers
    - 🐻 **Early Bear**: Trend reversed downward — go defensive
    - 💀 **Capitulation**: Panic selling, extreme fear — scary but often the best opportunity
    - 🌱 **Recovery**: Bottoming and starting to recover
    - 😐 **Sideways**: No clear trend — wait for direction
    """)

# ── Current regime display ──
st.markdown("### Current Status")
latest_color = REGIME_COLORS.get(latest_regime, "#6b7280")

col1, col2, col3 = st.columns(3)
col1.metric("Current Regime", latest_regime.upper().replace("_", " "), help="The market phase classification for the most recent day in our data.")

regime_counts = regimes.value_counts()
pct_in_regime = regime_counts.get(latest_regime, 0) / len(regimes) * 100
col2.metric("Days in This Regime", f"{regime_counts.get(latest_regime, 0)}", f"{pct_in_regime:.1f}% of history", help="How often the market has been in this regime throughout our dataset.")

# Current streak
days_in_current = 0
for r in regimes.iloc[::-1]:
    if r == latest_regime:
        days_in_current += 1
    else:
        break
col3.metric("Current Streak", f"{days_in_current} days", help="How many consecutive days we've been in this regime.")

# ── Regime interpretation ──
regime_advice = {
    "accumulation": ("🔄 ACCUMULATION", "Price has fallen significantly but is stabilizing. Historically, this is a good time to gradually build a position. The system's signal score typically reads high in this regime."),
    "early_bull": ("🚀 EARLY BULL", "The trend is turning upward. Cautious optimism is warranted. Moderate buying is typical here."),
    "bull_expansion": ("📈 BULL EXPANSION", "Strong uptrend in progress. This is where the biggest gains happen, but also where greed can lead to overexposure."),
    "late_bull": ("⚠️ LATE BULL", "Still rising but showing exhaustion. Consider taking some profits. Don't add new positions aggressively."),
    "blow_off": ("🚀 BLOW-OFF TOP", "Parabolic price spike — this often marks a cycle top. Very high risk. The system would typically recommend reducing exposure."),
    "distribution": ("📤 DISTRIBUTION", "Price near the top but weakening. Smart money is selling. Reduce exposure."),
    "early_bear": ("🐻 EARLY BEAR", "The trend has reversed downward. Go defensive. Don't try to catch falling knives."),
    "capitulation": ("💀 CAPITULATION", "Panic selling and extreme fear. Paradoxically, this is where the best opportunities are born — but it's terrifying to act on."),
    "recovery": ("🌱 RECOVERY", "Price is bottoming and starting to recover. Cautious accumulation is appropriate."),
    "sideways": ("😐 SIDEWAYS / UNCERTAIN", "No clear trend. The market is deciding which direction to go. Patience is key."),
}

if latest_regime in regime_advice:
    title, advice = regime_advice[latest_regime]
    st.info(f"**{title}** — {advice}")

st.divider()

# ── Charts ──
st.markdown("### Regime Distribution")
st.caption("How much time has ETH spent in each market phase? This helps you understand which regimes are common vs rare.")
col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(regime_distribution_chart(regimes), use_container_width=True)
with col_right:
    st.markdown("#### Regime Timeline")
    st.caption("Each dot shows the regime classification for each day. Look for patterns — how long does each regime last? How quickly does the market transition?")
    st.plotly_chart(regime_timeline_chart(regimes), use_container_width=True)

# ── Transition matrix ──
st.markdown("### Regime Transition Probabilities")
st.caption("If we're in regime X today, what's the probability of being in regime Y tomorrow? This helps anticipate what comes next.")

regime_list = list(REGIME_COLORS.keys())
transitions: dict[str, dict[str, int]] = {}
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
st.caption("💡 Read each row as: 'When in [regime], the market transitions to [column] X% of the time.' High values on the diagonal mean the regime tends to persist (momentum).")