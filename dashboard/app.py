"""Streamlit dashboard entry point."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Launch Streamlit multi-page dashboard."""

    pages = [
        st.Page("dashboard/pages/overview.py", title="Market Overview", icon="📊"),
        st.Page("dashboard/pages/regime.py", title="Current Regime", icon="🎯"),
        st.Page("dashboard/pages/signals.py", title="Signal Score", icon="📡"),
        st.Page("dashboard/pages/backtest.py", title="Historical Backtest", icon="📜"),
        st.Page("dashboard/pages/drawdowns.py", title="Drawdown Analysis", icon="📉"),
        st.Page("dashboard/pages/comparison.py", title="Strategy Comparison", icon="⚖️"),
        st.Page("dashboard/pages/monte_carlo.py", title="Monte Carlo", icon="🎲"),
        st.Page("dashboard/pages/staking.py", title="Staking Model", icon="⛏️"),
        st.Page("dashboard/pages/scenarios.py", title="Scenario Simulator", icon="🔮"),
        st.Page("dashboard/pages/sensitivity.py", title="Parameter Sensitivity", icon="🔧"),
        st.Page("dashboard/pages/trade_history.py", title="Trade History", icon="📋"),
    ]
    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()
