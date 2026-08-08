"""Slifer Test — interactive profit calculator.

Enter your own numbers and see exactly how much money you could make (or lose)
under different ETH investment scenarios.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import DARK_LAYOUT
from dashboard.components.style import inject_luxury_css

st.set_page_config(page_title="Slifer Test — ETH Cycle Engine", layout="wide", page_icon="💎")

inject_luxury_css()

# ── Luxury header ──
st.markdown("""
<div style='
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 24px 32px;
    margin: 16px 0 8px 0;
'>
    <h1 style='color:#ffffff;font-size:2rem;font-weight:800;letter-spacing:-0.03em;margin:0;'>💎 Slifer Test</h1>
    <p style='color:#e63946;font-size:0.9rem;font-weight:600;letter-spacing:0.15em;margin:4px 0 0 0;text-transform:uppercase;'>Profit Calculator & What-If Simulator</p>
    <p style='color:#777777;font-size:0.85rem;margin:8px 0 0 0;'>
    Enter your own numbers and instantly see how much money you could make — or lose — under different scenarios.
    </p>
</div>
""", unsafe_allow_html=True)

with st.expander("📖 How to use this calculator"):
    st.markdown("""
    This is your personal profit simulator. Here's how to use it:

    **Step 1:** Set your starting capital (how much money you're investing)
    **Step 2:** Set your buy price (what price you'd buy ETH at)
    **Step 3:** Set your target sell price (what price you'd sell at)
    **Step 4:** Adjust other settings (staking yield, time held, fees, taxes)
    **Step 5:** See your projected profit, ROI, and breakdown

    **The calculator accounts for:**
    - Trading fees and slippage (cost of buying and selling)
    - Staking yield (earn ETH while you hold)
    - Optional taxes (short-term vs long-term)
    - Multiple scenarios at once (compare 3 scenarios side-by-side)

    **⚠️ Important:** These are hypothetical projections, not predictions. Crypto is extremely volatile — ETH can drop 80%+ in bear markets. Never invest more than you can afford to lose.
    """)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# INPUT SECTION
# ════════════════════════════════════════════════════════════════════════════
st.markdown("## ⚙️ Your Settings")

col_input1, col_input2, col_input3, col_input4 = st.columns(4)

with col_input1:
    st.markdown("### 💰 Capital")
    starting_capital = st.number_input(
        "Starting Capital ($)", min_value=100, max_value=10_000_000, value=50_000, step=1_000,
        help="How much money you're starting with."
    )
    buy_price = st.number_input(
        "ETH Buy Price ($)", min_value=1.0, max_value=100_000.0, value=2_000.0, step=50.0,
        help="The price at which you'd buy ETH."
    )

with col_input2:
    st.markdown("### 🎯 Target")
    sell_price = st.number_input(
        "ETH Sell Price ($)", min_value=1.0, max_value=100_000.0, value=5_000.0, step=50.0,
        help="The price at which you'd sell ETH. Be realistic — ETH's all-time high was ~$4,800."
    )
    time_held_days = st.slider(
        "Time Held (days)", min_value=1, max_value=3650, value=365, step=30,
        help="How long you'd hold before selling. 365 = 1 year. Holding >1 year may qualify for lower long-term tax rates."
    )

with col_input3:
    st.markdown("### 🏦 Staking")
    staking_enabled = st.checkbox("Enable Staking", value=True, help="If checked, your ETH earns yield while you hold it.")
    staking_yield = st.slider(
        "Staking Yield (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1,
        help="Annual percentage yield from staking ETH. Current Ethereum staking rate is ~3%."
    )
    staking_compound = st.checkbox("Compound Daily", value=True, help="If checked, staking rewards are reinvested daily (faster growth).")

with col_input4:
    st.markdown("### 💸 Costs & Taxes")
    trading_fee = st.slider(
        "Trading Fee (%)", min_value=0.0, max_value=2.0, value=0.1, step=0.05,
        help="Fee per trade (buy and sell). Most exchanges charge 0.05-0.1%."
    )
    slippage = st.slider(
        "Slippage (%)", min_value=0.0, max_value=2.0, value=0.1, step=0.05,
        help="The difference between expected price and actual fill price. Higher for large orders."
    )
    enable_tax = st.checkbox("Enable Tax Modeling", value=False, help="If checked, apply capital gains tax to profits.")
    if enable_tax:
        if time_held_days >= 365:
            tax_rate = st.slider("Tax Rate (%)", min_value=0.0, max_value=50.0, value=20.0, step=1.0,
                help="Long-term capital gains rate (held >1 year). Typically 0-20% in the US.")
        else:
            tax_rate = st.slider("Tax Rate (%)", min_value=0.0, max_value=50.0, value=37.0, step=1.0,
                help="Short-term capital gains rate (held <1 year). Typically your income tax rate.")
        staking_tax_rate = st.slider("Staking Income Tax (%)", min_value=0.0, max_value=50.0, value=37.0, step=1.0,
            help="Tax on staking rewards. Taxed as ordinary income in most jurisdictions.")
    else:
        tax_rate = 0.0
        staking_tax_rate = 0.0

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# CALCULATION ENGINE
# ════════════════════════════════════════════════════════════════════════════

def calculate_scenario(
    capital: float, buy_price: float, sell_price: float, days_held: int,
    staking_on: bool, s_yield: float, compound: bool,
    fee_pct: float, slip_pct: float, tax_on: bool, cg_tax: float, stake_tax: float,
) -> dict:
    """Calculate full profit breakdown for a scenario."""

    # ── Buy ──
    fee_buy = capital * (fee_pct / 100)
    slip_buy = capital * (slip_pct / 100)
    net_buy_capital = capital - fee_buy - slip_buy
    eth_bought = net_buy_capital / buy_price

    # ── Staking ──
    staking_rewards_eth = 0.0
    staking_rewards_usd = 0.0
    total_eth = eth_bought

    if staking_on and s_yield > 0:
        daily_rate = (s_yield / 100) / 365
        if compound:
            for _day in range(days_held):
                reward = total_eth * daily_rate
                total_eth += reward
                staking_rewards_eth += reward
        else:
            # Simple interest — rewards not reinvested
            staking_rewards_eth = eth_bought * daily_rate * days_held
            total_eth = eth_bought + staking_rewards_eth

    # ── Sell ──
    gross_sell = total_eth * sell_price
    fee_sell = gross_sell * (fee_pct / 100)
    slip_sell = gross_sell * (slip_pct / 100)
    net_sell = gross_sell - fee_sell - slip_sell

    # ── Taxes ──
    capital_gain = net_sell - net_buy_capital
    tax_on_gain = 0.0
    tax_on_staking = 0.0

    if tax_on:
        if capital_gain > 0:
            tax_on_gain = capital_gain * (cg_tax / 100)
        if staking_rewards_eth > 0:
            staking_rewards_usd = staking_rewards_eth * sell_price
            tax_on_staking = staking_rewards_usd * (stake_tax / 100)

    total_taxes = tax_on_gain + tax_on_staking
    after_tax_proceeds = net_sell - total_taxes

    # ── Summary ──
    total_costs = fee_buy + slip_buy + fee_sell + slip_sell
    total_profit = after_tax_proceeds - capital
    roi = (total_profit / capital) * 100 if capital > 0 else 0
    annualized_roi = ((after_tax_proceeds / capital) ** (365 / max(days_held, 1)) - 1) * 100 if capital > 0 and days_held > 0 else 0
    price_multiple = sell_price / buy_price

    return {
        "starting_capital": capital,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "eth_bought": eth_bought,
        "total_eth_at_sell": total_eth,
        "staking_rewards_eth": staking_rewards_eth,
        "staking_rewards_usd": staking_rewards_eth * sell_price,
        "gross_sell_value": gross_sell,
        "trading_costs": total_costs,
        "total_taxes": total_taxes,
        "after_tax_proceeds": after_tax_proceeds,
        "total_profit": total_profit,
        "roi_pct": roi,
        "annualized_roi_pct": annualized_roi,
        "price_multiple": price_multiple,
        "days_held": days_held,
    }


# ── Main scenario ──
result = calculate_scenario(
    starting_capital, buy_price, sell_price, time_held_days,
    staking_enabled, staking_yield, staking_compound,
    trading_fee, slippage, enable_tax, tax_rate, staking_tax_rate,
)

# ════════════════════════════════════════════════════════════════════════════
# RESULTS — BIG NUMBERS
# ════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Your Results")

profit_color = "#22c55e" if result["total_profit"] >= 0 else "#ef4444"

col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)

col_r1.metric(
    "Total Profit / Loss",
    f"${result['total_profit']:,.0f}",
    help="Your net profit or loss after all fees, costs, and taxes."
)
col_r2.metric(
    "ROI (%)",
    f"{result['roi_pct']:.1f}%",
    help="Return on investment — total profit divided by starting capital."
)
col_r3.metric(
    "Annualized ROI",
    f"{result['annualized_roi_pct']:.1f}%",
    help="What your yearly return would be if the total return was spread evenly over the holding period."
)
col_r4.metric(
    "ETH Accumulated",
    f"{result['total_eth_at_sell']:.4f} ETH",
    help="Total ETH at the time of sell, including staking rewards."
)
col_r5.metric(
    "Price Multiple",
    f"{result['price_multiple']:.1f}x",
    help="How many times the price multiplied. 2x means ETH doubled."
)

# ── Profit / loss banner ──
if result["total_profit"] >= 0:
    st.success(f"💰 **You'd make ${result['total_profit']:,.0f} profit** — your ${starting_capital:,.0f} turned into ${result['after_tax_proceeds']:,.0f} over {time_held_days} days.")
else:
    st.error(f"📉 **You'd lose ${abs(result['total_profit']):,.0f}** — your ${starting_capital:,.0f} shrank to ${result['after_tax_proceeds']:,.0f} over {time_held_days} days.")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# BREAKDOWN TABLE
# ════════════════════════════════════════════════════════════════════════════
st.markdown("### 💼 Full Breakdown")
st.caption("Every dollar accounted for — from your starting capital to your final after-tax proceeds.")

breakdown_data = {
    "Item": [
        "Starting Capital",
        f"Buy Fee ({trading_fee}%)",
        f"Buy Slippage ({slippage}%)",
        "Capital Available for ETH",
        f"ETH Bought @ ${buy_price:,.0f}",
        "",
        f"Staking Rewards ({staking_yield}% APY, {'compounded' if staking_compound else 'simple'})",
        "Total ETH at Sale",
        "",
        f"Gross Sale Value @ ${sell_price:,.0f}",
        f"Sell Fee ({trading_fee}%)",
        f"Sell Slippage ({slippage}%)",
        "Net Sale Proceeds",
    ],
    "USD": [
        f"${starting_capital:,.2f}",
        f"-${result['trading_costs']/2:,.2f}" if result['trading_costs'] > 0 else "$0.00",
        f"-${result['trading_costs']/2:,.2f}" if result['trading_costs'] > 0 else "$0.00",
        f"${starting_capital - result['trading_costs']/2:,.2f}",
        f"{result['eth_bought']:.6f} ETH",
        "",
        f"+{result['staking_rewards_eth']:.6f} ETH (${result['staking_rewards_usd']:,.2f})" if staking_enabled else "Disabled",
        f"{result['total_eth_at_sell']:.6f} ETH",
        "",
        f"${result['gross_sell_value']:,.2f}",
        f"-${result['trading_costs']/2:,.2f}" if result['trading_costs'] > 0 else "$0.00",
        f"-${result['trading_costs']/2:,.2f}" if result['trading_costs'] > 0 else "$0.00",
        f"${result['gross_sell_value'] - result['trading_costs']:,.2f}",
    ],
}

if enable_tax:
    breakdown_data["Item"].extend([
        "",
        f"Capital Gains Tax ({tax_rate}%)",
        f"Staking Income Tax ({staking_tax_rate}%)",
        "Total Taxes",
        "",
        "Final After-Tax Value",
        "Total Profit / Loss",
    ])
    breakdown_data["USD"].extend([
        "",
        f"-${result['total_taxes'] - (result['staking_rewards_usd'] * staking_tax_rate / 100 if staking_enabled else 0):,.2f}" if result['total_taxes'] > 0 else "$0.00",
        f"-${result['staking_rewards_usd'] * staking_tax_rate / 100:,.2f}" if staking_enabled and result['staking_rewards_usd'] > 0 else "$0.00",
        f"-${result['total_taxes']:,.2f}" if result['total_taxes'] > 0 else "$0.00",
        "",
        f"${result['after_tax_proceeds']:,.2f}",
        f"{'+' if result['total_profit'] >= 0 else ''}${result['total_profit']:,.2f}",
    ])
else:
    breakdown_data["Item"].extend([
        "",
        "Final Value (no tax)",
        "Total Profit / Loss",
    ])
    breakdown_data["USD"].extend([
        "",
        f"${result['after_tax_proceeds']:,.2f}",
        f"{'+' if result['total_profit'] >= 0 else ''}${result['total_profit']:,.2f}",
    ])

st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# GROWTH CHART
# ════════════════════════════════════════════════════════════════════════════
st.markdown("### 📈 Portfolio Growth Over Time")
st.caption("Watch your portfolio grow day by day. The gap between the two lines is your staking yield — 'free' ETH you earn while holding.")

# Build day-by-day growth curve
days = list(range(time_held_days + 1))
portfolio_values = []
eth_values = []

daily_rate = (staking_yield / 100) / 365 if staking_enabled else 0
current_eth = result["eth_bought"]
current_value_no_stake = result["eth_bought"] * buy_price  # value without staking

for day in days:
    # Interpolate price linearly from buy to sell
    t = day / max(time_held_days, 1)
    current_price = buy_price + (sell_price - buy_price) * t

    # With staking
    portfolio_values.append(current_eth * current_price)

    # Without staking (just price appreciation)
    eth_values.append(result["eth_bought"] * current_price)

    # Compound staking
    if staking_enabled and staking_compound and day < time_held_days:
        reward = current_eth * daily_rate
        current_eth += reward

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=days, y=portfolio_values,
    name="With Staking", line={"color": "#e63946", "width": 2.5},
    fill="tozeroy", fillcolor="rgba(230,57,70,0.06)",
))
fig.add_trace(go.Scatter(
    x=days, y=eth_values,
    name="Without Staking", line={"color": "#666666", "width": 1.5, "dash": "dash"},
))
fig.update_layout(
    title=f"Portfolio Value Over {time_held_days} Days (${buy_price:,.0f} → ${sell_price:,.0f})",
    xaxis_title="Days Held", yaxis_title="Portfolio Value ($)",
    **DARK_LAYOUT,
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# Staking benefit
if staking_enabled and result["staking_rewards_eth"] > 0:
    staking_benefit_usd = result["staking_rewards_usd"]
    st.info(f"⛏️ **Staking earned you {result['staking_rewards_eth']:.6f} extra ETH** — worth ${staking_benefit_usd:,.2f} at sell price. That's 'free' ETH on top of your price gains.")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SCENARIO COMPARISON — 3 scenarios side by side
# ════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔀 Scenario Comparison")
st.caption("Compare your main scenario against a more conservative and more aggressive version. See how different sell prices change your profit.")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    st.markdown("#### 🐻 Conservative")
    conservative_sell = st.number_input("Sell Price — Conservative ($)", value=sell_price * 0.5, step=100.0, key="cons_sell")

with col_s2:
    st.markdown("#### ⚖️ Your Scenario")
    st.markdown(f"**${buy_price:,.0f} → ${sell_price:,.0f}**")

with col_s3:
    st.markdown("#### 🚀 Aggressive")
    aggressive_sell = st.number_input("Sell Price — Aggressive ($)", value=sell_price * 2.0, step=100.0, key="agg_sell")

# Calculate all three
scenarios = {
    "🐻 Conservative": calculate_scenario(
        starting_capital, buy_price, conservative_sell, time_held_days,
        staking_enabled, staking_yield, staking_compound,
        trading_fee, slippage, enable_tax, tax_rate, staking_tax_rate,
    ),
    "⚖️ Your Scenario": result,
    "🚀 Aggressive": calculate_scenario(
        starting_capital, buy_price, aggressive_sell, time_held_days,
        staking_enabled, staking_yield, staking_compound,
        trading_fee, slippage, enable_tax, tax_rate, staking_tax_rate,
    ),
}

# Comparison table
comp_rows = []
for name, sc in scenarios.items():
    comp_rows.append({
        "Scenario": name,
        "Sell Price": f"${sc['sell_price']:,.0f}",
        "Price Multiple": f"{sc['price_multiple']:.1f}x",
        "ETH at Sale": f"{sc['total_eth_at_sell']:.4f}",
        "Staking Rewards": f"{sc['staking_rewards_eth']:.6f} ETH",
        "Trading Costs": f"${sc['trading_costs']:,.2f}",
        "Taxes": f"${sc['total_taxes']:,.2f}",
        "Final Value": f"${sc['after_tax_proceeds']:,.0f}",
        "Profit / Loss": f"{'+' if sc['total_profit'] >= 0 else ''}${sc['total_profit']:,.0f}",
        "ROI %": f"{sc['roi_pct']:.1f}%",
    })

st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

# Comparison chart
fig2 = go.Figure()
scenario_names = list(scenarios.keys())
finals = [sc["after_tax_proceeds"] for sc in scenarios.values()]
profits = [sc["total_profit"] for sc in scenarios.values()]
colors_bar = ["#ef4444" if p < 0 else "#e63946" for p in profits]

fig2.add_trace(go.Bar(
    x=scenario_names, y=finals,
    name="Final Value", marker_color=colors_bar,
    marker_line_color="#ffffff", marker_line_width=0.5,
))
fig2.add_hline(y=starting_capital, line_color="#666666", line_dash="dash", annotation_text=f"Starting Capital (${starting_capital:,.0f})")
fig2.update_layout(title="Final Portfolio Value by Scenario", yaxis_title="USD", **{k: v for k, v in DARK_LAYOUT.items() if k != "title"})
fig2.update_layout(height=350)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# WHAT-IF GRID — price sensitivity heatmap
# ════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔥 What-If Heatmap")
st.caption("What profit would you make at different buy and sell prices? Each cell shows your ROI. Find the cell that matches your scenario.")

# Build heatmap grid
buy_range = np.linspace(buy_price * 0.5, buy_price * 1.5, 12)
sell_range = np.linspace(sell_price * 0.3, sell_price * 2.0, 12)

roi_grid = np.zeros((len(buy_range), len(sell_range)))
for i, bp in enumerate(buy_range):
    for j, sp in enumerate(sell_range):
        sc = calculate_scenario(
            starting_capital, bp, sp, time_held_days,
            staking_enabled, staking_yield, staking_compound,
            trading_fee, slippage, enable_tax, tax_rate, staking_tax_rate,
        )
        roi_grid[i, j] = sc["roi_pct"]

import plotly.express as px

fig3 = px.imshow(
    roi_grid,
    x=[f"${sp:,.0f}" for sp in sell_range],
    y=[f"${bp:,.0f}" for bp in buy_range],
    title="ROI (%) by Buy Price (Y) vs Sell Price (X)",
    color_continuous_scale=["#ef4444", "#1a1a1a", "#22c55e"],
    labels={"x": "Sell Price", "y": "Buy Price", "color": "ROI %"},
    aspect="auto",
    text_auto=".0f",
)
fig3.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#121212", font={"color": "#f5f5f5"}, height=450)
st.plotly_chart(fig3, use_container_width=True)
st.caption("💡 **Green = profit, Red = loss.** Find your buy price on the left axis and your target sell price on the bottom. The number in each cell is your ROI percentage. The darker the green, the more money you make.")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# DRAWDOWN WARNING
# ════════════════════════════════════════════════════════════════════════════
st.markdown("## ⚠️ Reality Check")
st.warning("""
**Before you invest, consider:**

- ETH has historically dropped **80%+** during bear markets (2018, 2022)
- If you buy at $4,000 and ETH drops to $800, you lose **80% of your investment**
- The calculator above assumes a linear price path — real ETH prices are extremely volatile
- Staking rewards are paid in ETH — if ETH's price crashes, your staking rewards are worth less too
- This calculator does NOT account for the emotional difficulty of holding through a -80% drawdown
- **Never invest more than you can afford to lose entirely**

**The Slifer Test shows you the upside. The Drawdown Analysis page shows you the downside. Look at both.**
""")