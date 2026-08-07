"""Reusable Plotly chart components for the ETH Cycle Engine dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# Dark theme colors
BG = "#0a0a0b"
PANEL = "#15151a"
GRID = "#222228"
TEXT = "#e0e0e8"
GREEN = "#00d68f"
RED = "#ff3860"
BLUE = "#3b82f6"
PURPLE = "#8b5cf6"
ORANGE = "#f59e0b"
GRAY = "#6b7280"

DARK_LAYOUT = {
    "paper_bgcolor": BG,
    "plot_bgcolor": PANEL,
    "font": {"color": TEXT, "family": "Inter, sans-serif"},
    "xaxis": {"gridcolor": GRID, "zerolinecolor": GRID},
    "yaxis": {"gridcolor": GRID, "zerolinecolor": GRID},
    "margin": {"l": 10, "r": 10, "t": 40, "b": 10},
    "legend": {"bgcolor": PANEL, "bordercolor": GRID},
}

REGIME_COLORS = {
    "accumulation": "#3b82f6",
    "early_bull": "#00d68f",
    "bull_expansion": "#00d68f",
    "late_bull": "#f59e0b",
    "blow_off": "#ff3860",
    "distribution": "#f59e0b",
    "early_bear": "#ff3860",
    "capitulation": "#ff3860",
    "recovery": "#3b82f6",
    "sideways": "#6b7280",
}


def price_chart_with_signals(
    prices: pd.DataFrame,
    buy_signals: pd.DataFrame | None = None,
    sell_signals: pd.DataFrame | None = None,
    regimes: pd.Series | None = None,
) -> go.Figure:
    """ETH price chart with buy/sell markers and regime shading."""

    close = prices["close"] if isinstance(prices, pd.DataFrame) and "close" in prices else pd.Series(prices)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=close.index, y=close, name="ETH Close", line={"color": BLUE, "width": 1.5}))

    if buy_signals is not None and len(buy_signals):
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=buy_signals["price"] if "price" in buy_signals else buy_signals.iloc[:, 0],
                mode="markers",
                name="Buy",
                marker={"color": GREEN, "symbol": "triangle-up", "size": 10},
            )
        )
    if sell_signals is not None and len(sell_signals):
        fig.add_trace(
            go.Scatter(
                x=sell_signals.index,
                y=sell_signals["price"] if "price" in sell_signals else sell_signals.iloc[:, 0],
                mode="markers",
                name="Sell",
                marker={"color": RED, "symbol": "triangle-down", "size": 10},
            )
        )
    # Regime shading
    if regimes is not None and len(regimes):
        for regime_val, color in REGIME_COLORS.items():
            mask = regimes == regime_val
            if mask.any():
                idxs = mask[mask].index
                for idx in idxs:
                    fig.add_vrect(
                        x0=idx,
                        x1=idx + pd.Timedelta(days=1),
                        fillcolor=color,
                        opacity=0.05,
                        layer="below",
                        line_width=0,
                    )

    title_suffix = f" — Latest regime: {regimes.iloc[-1]}" if regimes is not None and len(regimes) else ""
    fig.update_layout(title=f"ETH/USD Price{title_suffix}", **DARK_LAYOUT)
    fig.update_layout(height=500)
    return fig


def equity_curve_chart(equity: pd.Series, benchmark_equity: pd.Series | None = None, benchmark_name: str = "Buy & Hold") -> go.Figure:
    """Strategy vs benchmark equity curve."""

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=equity.index, y=equity, name="Strategy", line={"color": PURPLE, "width": 2}))
    if benchmark_equity is not None:
        fig.add_trace(go.Scatter(x=benchmark_equity.index, y=benchmark_equity, name=benchmark_name, line={"color": GRAY, "width": 1.5, "dash": "dash"}))
    fig.update_layout(title="Portfolio Equity Curve", yaxis_title="USD", **DARK_LAYOUT)
    fig.update_layout(height=450)
    return fig


def drawdown_chart(equity: pd.Series) -> go.Figure:
    """Underwater drawdown plot."""

    dd = equity / equity.cummax() - 1
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dd.index,
            y=dd * 100,
            fill="tozeroy",
            name="Drawdown",
            line={"color": RED, "width": 0.5},
            fillcolor="rgba(255,56,96,0.3)",
        )
    )
    fig.update_layout(title="Drawdown from Peak (%)", yaxis_title="Drawdown %", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig


def exposure_chart(cash: pd.Series, eth_value: pd.Series) -> go.Figure:
    """Cash vs ETH exposure stacked area."""

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cash.index, y=cash, stackgroup="one", name="Cash", line={"color": BLUE, "width": 0}))
    fig.add_trace(go.Scatter(x=eth_value.index, y=eth_value, stackgroup="one", name="ETH Value", line={"color": PURPLE, "width": 0}))
    fig.update_layout(title="Cash vs ETH Exposure", yaxis_title="USD", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig


def signal_confidence_chart(scores: pd.Series) -> go.Figure:
    """Signal confidence 0-100 over time with colored bands."""

    fig = go.Figure()
    # Background bands
    bands = [
        (0, 20, "rgba(255,56,96,0.08)", "Strong Sell"),
        (20, 41, "rgba(255,56,96,0.04)", "Reduce"),
        (41, 60, "rgba(107,114,128,0.04)", "Neutral"),
        (60, 75, "rgba(0,214,143,0.04)", "Accumulate"),
        (75, 90, "rgba(0,214,143,0.08)", "Strong Accum."),
        (90, 101, "rgba(0,214,143,0.12)", "Extreme Accum."),
    ]
    for lo, hi, color, _label in bands:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=color, layer="below", line_width=0)
    fig.add_trace(go.Scatter(x=scores.index, y=scores, name="Signal Score", line={"color": ORANGE, "width": 1.5}))
    fig.update_layout(title="Signal Confidence Score (0-100)", yaxis={"range": [0, 100]}, **DARK_LAYOUT)
    fig.update_layout(height=400)
    return fig


def rolling_sharpe_chart(returns: pd.Series, window: int = 252) -> go.Figure:
    """Rolling annualized Sharpe ratio."""

    sharpe = returns.rolling(window, min_periods=max(window // 2, 20)).mean() / returns.rolling(window, min_periods=max(window // 2, 20)).std() * (365**0.5)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sharpe.index, y=sharpe, name=f"Rolling Sharpe ({window}d)", line={"color": GREEN, "width": 1.5}))
    fig.add_hline(y=0, line_color=GRAY, line_dash="dash")
    fig.update_layout(title=f"Rolling Sharpe Ratio ({window}-day window)", yaxis_title="Sharpe", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig


def rolling_volatility_chart(returns: pd.Series, window: int = 21) -> go.Figure:
    """Rolling annualized volatility."""

    vol = returns.rolling(window, min_periods=max(window // 2, 10)).std() * (365**0.5)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=vol.index, y=vol * 100, name=f"Rolling Vol ({window}d)", line={"color": ORANGE, "width": 1.5}))
    fig.update_layout(title=f"Rolling Annualized Volatility ({window}-day window)", yaxis_title="Volatility %", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig


def regime_distribution_chart(regimes: pd.Series) -> go.Figure:
    """Bar chart of regime distribution."""

    counts = regimes.value_counts()
    colors = [REGIME_COLORS.get(r, GRAY) for r in counts.index]
    fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=colors))
    fig.update_layout(title="Regime Distribution (full history)", xaxis_title="Regime", yaxis_title="Days", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig


def regime_timeline_chart(regimes: pd.Series) -> go.Figure:
    """Regime classification over time as colored scatter."""

    fig = go.Figure()
    for regime_val, color in REGIME_COLORS.items():
        mask = regimes == regime_val
        if mask.any():
            subset = regimes[mask]
            fig.add_trace(
                go.Scatter(
                    x=subset.index,
                    y=[regime_val] * len(subset),
                    mode="markers",
                    name=regime_val,
                    marker={"color": color, "size": 3},
                )
            )
    fig.update_layout(title="Regime Timeline", yaxis={"categoryorder": "array", "categoryarray": list(REGIME_COLORS.keys())}, **DARK_LAYOUT)
    fig.update_layout(height=400)
    return fig


def monte_carlo_chart(percentiles: dict) -> go.Figure:
    """Monte Carlo percentile fan chart."""

    fig = go.Figure()
    if "p10" in percentiles:
        fig.add_trace(go.Bar(x=["P10", "P25", "P50", "P75", "P90"], y=[percentiles["p10"], percentiles["p25"], percentiles["p50"], percentiles["p75"], percentiles["p90"]], marker_color=[RED, ORANGE, GRAY, GREEN, GREEN]))
    fig.update_layout(title="Monte Carlo: Final Portfolio Multiple by Percentile", yaxis_title="Multiple (1x = breakeven)", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig


def strategy_comparison_chart(results: dict) -> go.Figure:
    """Bar chart comparing strategy metrics."""

    names = list(results.keys())
    sharpe_vals = [results[n].get("sharpe_ratio", 0) for n in names]
    fig = go.Figure(go.Bar(x=names, y=sharpe_vals, marker_color=[PURPLE if n == "Signal Driven" else BLUE for n in names]))
    fig.update_layout(title="Sharpe Ratio Comparison", yaxis_title="Sharpe", **DARK_LAYOUT)
    fig.update_layout(height=350)
    return fig