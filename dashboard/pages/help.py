"""Help & Glossary — explains every term used in the dashboard."""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Help & Glossary", layout="wide", page_icon="📖")

from dashboard.components.style import inject_luxury_css
inject_luxury_css()

st.title("📖 Help & Glossary")
st.markdown("New to crypto or quantitative trading? This page explains every term used throughout the dashboard in plain English.")

# Luxury brand header
st.markdown("""
<div style='
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 24px 32px;
    margin: 16px 0 8px 0;
'>
    <h1 style='
        color: #ffffff;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0;
    '>ETH CYCLE ENGINE</h1>
    <p style='
        color: #e63946;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        margin: 4px 0 0 0;
        text-transform: uppercase;
    '>Market-Cycle Backtesting & Simulation</p>
    <p style='color: #777777; font-size: 0.85rem; margin: 8px 0 0 0;'>
    Research whether observable market conditions create a repeatable statistical edge — not a price prediction toy.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

st.header("Market Basics")

terms = [
    ("ETH/USD", "Ethereum priced in US Dollars. When we say 'ETH price,' this is what we mean."),
    ("OHLCV", "Open, High, Low, Close, Volume — the 5 data points for each trading day. Open = first price of the day, High = highest price, Low = lowest price, Close = last price, Volume = how much was traded."),
    ("Bull Market", "A period when prices are generally rising over months or years. Think: optimism, buying pressure."),
    ("Bear Market", "A period when prices are generally falling. Think: pessimism, selling pressure. ETH dropped ~80%+ in 2018 and 2022."),
    ("Drawdown", "How far the price has fallen from its highest point. If ETH peaked at $4,800 and is now $2,400, the drawdown is -50%. This is the most important risk metric."),
    ("Volatility", "How much the price swings up and down. High volatility = big daily moves (risky but opportunity). Low volatility = calm (safer but boring)."),
    ("Market Cap", "Total value of all ETH in existence = ETH price × total ETH supply."),
]

for term, definition in terms:
    st.markdown(f"**{term}** — {definition}")

st.divider()
st.header("Technical Indicators")

indicators = [
    ("EMA (Exponential Moving Average)", "The average price over a period, giving more weight to recent prices. We use 20-day (short-term), 50-day (medium), 100-day, and 200-day (long-term trend). When price is above its 200-day EMA, the long-term trend is up."),
    ("RSI (Relative Strength Index)", "A 0-100 scale measuring whether ETH is overbought or oversold. Above 70 = potentially overbought (expensive). Below 30 = potentially oversold (cheap). This is a momentum indicator, not a buy/sell signal on its own."),
    ("MACD (Moving Average Convergence Divergence)", "Compares short-term and long-term moving averages to detect trend changes. When MACD crosses above its signal line, it suggests upward momentum."),
    ("ATR (Average True Range)", "Measures average daily price movement. Higher ATR = more volatile market. Used for setting stop-loss levels."),
    ("Bollinger Bands", "Lines drawn above and below the moving average showing the normal price range. When price touches the upper band, it may be overextended. Lower band = potentially cheap."),
    ("Rate of Change (ROC)", "How fast the price is changing over a set period. High positive ROC = strong upward move. High negative ROC = sharp decline."),
]

for term, definition in indicators:
    st.markdown(f"**{term}** — {definition}")

st.divider()
st.header("Market Regimes")
st.markdown("The system classifies each day into one of 10 'regimes' — the current state of the market. Understanding the regime helps you know whether to be aggressive, cautious, or patient.")

regimes = [
    ("🔄 Accumulation", "Price has fallen significantly but is stabilizing. Smart money is quietly buying. This is often a good time to start building a position gradually."),
    ("🚀 Early Bull", "Price is recovering, short-term trend turning up. Cautiously optimistic. Moderate buying."),
    ("📈 Bull Expansion", "Strong uptrend. Price above all major moving averages. Higher highs, higher lows. This is where the biggest gains happen, but also where greed kicks in."),
    ("⚠️ Late Bull", "Still rising but showing signs of exhaustion. RSI persistently high, volume declining. Time to start thinking about exits."),
    ("🚀 Blow-Off Top", "Parabolic price spike. Extreme RSI, massive volume. Often marks the cycle top. Very dangerous to buy here."),
    ("📤 Distribution", "Price near the top but starting to weaken. Smart money is selling to late buyers. Reduce exposure."),
    ("🐻 Early Bear", "Trend has reversed. Price below key moving averages. Lower highs, lower lows. Defensive mode."),
    ("💀 Capitulation", "Panic selling. Massive drawdowns, extreme fear. Paradoxically, this is where the best opportunities are born — but it's terrifying to buy."),
    ("🌱 Recovery", "Price bottoming and starting to recover. Cautious accumulation."),
    ("😐 Sideways / Uncertain", "No clear trend. Price oscillating in a range. Wait for clarity."),
]

for emoji_name, definition in regimes:
    st.markdown(f"**{emoji_name}** — {definition}")

st.divider()
st.header("Signal Score (0-100)")

st.markdown("""
The signal score is the system's confidence level for buying or selling. It combines 8 different sub-scores into one number:

| Score Range | Label | What It Means | What You'd Do |
|-------------|-------|---------------|---------------|
| 0-20 | Strong Sell | Extreme caution — multiple warning signs | Reduce exposure significantly |
| 21-40 | Reduce | Bearish signals building up | Start trimming positions |
| 41-59 | Neutral | No clear edge in either direction | Hold and wait |
| 60-74 | Accumulate | Favorable conditions building | Start buying in small tranches |
| 75-89 | Strong Accumulate | Strong buying conditions | Buy more aggressively |
| 90-100 | Extreme Accumulate | Rare opportunity — multiple signals aligned | Deploy capital (within risk limits) |
""")

st.markdown("""
**Sub-scores that make up the total:**
- **Valuation** (20%): Is ETH cheap or expensive relative to its history? Deep drawdowns = cheaper.
- **Trend** (15%): Are moving averages pointing up or down?
- **Momentum** (15%): Is RSI oversold or overbought? Is MACD turning?
- **Volatility** (10%): Is volatility high (panic = opportunity) or low (calm)?
- **Derivatives** (10%): Funding rates, liquidations (only available with paid data).
- **On-Chain** (10%): Exchange flows, MVRV (only available with paid data).
- **Macro** (10%): Stock market trend, dollar strength, interest rates.
- **Regime** (10%): What market phase are we in? Accumulation = high score.
""")

st.divider()
st.header("Performance Metrics")

metrics = [
    ("CAGR (Compound Annual Growth Rate)", "The average yearly return if the investment grew at a steady rate. A CAGR of 30% means your money grows 30% per year on average."),
    ("Total Return", "How much your portfolio grew from start to finish. A 200% total return means your $50,000 turned into $150,000."),
    ("Max Drawdown", "The worst peak-to-trough decline. A -90% max drawdown means at one point, your portfolio lost 90% of its value from its highest point. This is the scariest metric."),
    ("Sharpe Ratio", "Risk-adjusted return. Above 1.0 is good, above 2.0 is excellent. It measures how much return you get per unit of risk taken. A high Sharpe with a low return can be better than a high return with a terrible Sharpe."),
    ("Sortino Ratio", "Like Sharpe but only counts downside volatility. Better for crypto because upside volatility (price going up fast) isn't actually risk."),
    ("Calmar Ratio", "CAGR divided by max drawdown. Tells you if the returns were worth the worst pain you had to endure."),
    ("Win Rate", "Percentage of trades that were profitable. Note: a 40% win rate with 3:1 reward/risk can still be very profitable."),
    ("Value at Risk (VaR)", "The maximum you'd expect to lose on a bad day (95% confidence). A -6.5% VaR means on a bad day (1-in-20), you'd lose about 6.5%."),
    ("Conditional VaR (CVaR)", "If things go worse than VaR (the worst 5% of days), this is the average loss. It's the 'how bad is really bad' metric."),
]

for term, definition in metrics:
    st.markdown(f"**{term}** — {definition}")

st.divider()
st.header("Monte Carlo Simulation")

st.markdown("""
Monte Carlo simulation runs thousands of possible futures to see the range of outcomes.

**Think of it like this:** Instead of saying "ETH will go up 30% next year," Monte Carlo says "here are 2,000 possible futures. In 60% of them you make money, in 40% you lose. Here's what the worst-case looks like."

**Key outputs:**
- **P10 (10th percentile):** The bad outcome — 1-in-10 chance of this or worse
- **P50 (Median):** The middle outcome — 50% chance of doing better, 50% worse
- **P90 (90th percentile):** The good outcome — 1-in-10 chance of this or better
- **P(Loss):** Probability of losing money
- **P(50%+ Drawdown):** Probability of your portfolio being cut in half at some point
""")

st.divider()
st.header("Staking")

st.markdown("""
**Staking** is like earning interest on a savings account, but with ETH. You lock up your ETH to help secure the Ethereum network, and in return you earn more ETH.

- **Annual Yield:** The % of your staked ETH you earn per year. Default assumption: 3% (so 100 ETH becomes ~103 ETH after a year)
- **Compounding:** Rewards are added to your staked balance, so you earn yield on your yield. Daily compounding = rewards added every day.
- **Lockup:** ETH may be locked for a period during which you can't sell. Our default assumes no lockup, but real staking has withdrawal delays.
- **Slashing Risk:** If your validator misbehaves, a portion of staked ETH can be confiscated. We assume 0% but real risk exists.
""")

st.divider()
st.header("Important Disclaimers")

st.warning("""
⚠️ This is a research and education tool, NOT financial advice.

- Past performance does not guarantee future results
- Backtests can be misleading — strategies that worked historically may fail going forward
- Monte Carlo simulations are based on historical patterns, not predictions of the future
- The signal score is a statistical analysis, not a guarantee
- Crypto is extremely volatile — never invest more than you can afford to lose
- Always do your own research and consult a financial advisor before making investment decisions
""")