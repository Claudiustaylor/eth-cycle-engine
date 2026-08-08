"""Streamlit dashboard entry point."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Launch Streamlit multi-page dashboard."""

    pages = [
        st.Page("pages/help.py", title="Help & Glossary", icon="📖"),
        st.Page("pages/slifer_test.py", title="Slifer Test", icon="💎"),
        st.Page("pages/overview.py", title="Market Overview", icon="📊"),
        st.Page("pages/regime.py", title="Current Regime", icon="🎯"),
        st.Page("pages/signals.py", title="Signal Score", icon="📡"),
        st.Page("pages/backtest.py", title="Historical Backtest", icon="📜"),
        st.Page("pages/drawdowns.py", title="Drawdown Analysis", icon="📉"),
        st.Page("pages/comparison.py", title="Strategy Comparison", icon="⚖️"),
        st.Page("pages/monte_carlo.py", title="Monte Carlo", icon="🎲"),
        st.Page("pages/staking.py", title="Staking Model", icon="⛏️"),
        st.Page("pages/scenarios.py", title="Scenario Simulator", icon="🔮"),
        st.Page("pages/sensitivity.py", title="Parameter Sensitivity", icon="🔧"),
        st.Page("pages/trade_history.py", title="Trade History", icon="📋"),
    ]
    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()