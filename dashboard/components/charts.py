"""Reusable Plotly chart components for the ETH Cycle Engine dashboard.

Luxury black / red / white color palette.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# ── Luxury Black / Red / White Palette ──────────────────────────────────────
BG       = "#0a0a0a"   # near-black background
PANEL    = "#121212"   # slightly lighter panel
CARD     = "#1a1a1a"   # card / inner panel
GRID     = "#2a2a2a"   # subtle grid lines
TEXT     = "#f5f5f5"   # off-white text
TEXT_DIM = "#999999"   # dimmed text
WHITE    = "#ffffff"

# Accent colors — red family
RED      = "#e63946"   # primary red (crimson)
RED_DARK = "#b71c1c"   # deep red
RED_LITE = "#ff6b6b"   # light red
CRIMSON  = "#dc143c"   # crimson accent

# Functional colors (kept minimal, within the palette)
GREEN    = "#22c55e"   # positive (used sparingly)
RED_NEG  = "#ef4444"   # negative
GOLD     = "#f59e0b"   # warning / highlight
GRAY     = "#666666"   # neutral gray
SILVER   = "#888888"   # silver accent

DARK_LAYOUT = {
    "paper_bgcolor": BG,
    "plot_bgcolor": PANEL,
    "font": {"color": TEXT, "family": "Inter, -apple-system, sans-serif", "size": 13},
    "xaxis": {
        "gridcolor": GRID,
        "zerolinecolor": GRID,
        "showline": True,
        "linecolor": GRID,
        "tickfont": {"color": TEXT_DIM, "size": 11},
    },
    "yaxis": {
        "gridcolor": GRID,
        "zerolinecolor": GRID,
        "showline": True,
        "linecolor": GRID,
        "tickfont": {"color": TEXT_DIM, "size": 11},
    },
    "margin": {"l": 10, "r": 10, "t": 50, "b": 10},
    "legend": {
        "bgcolor": CARD,
        "bordercolor": GRID,
        "font": {"color": TEXT_DIM, "size": 12},
    },
    "title": {
        "font": {"color": WHITE, "size": 16, "family": "Inter, sans-serif"},
        "x": 0.02,
    },
    "hoverlabel": {
        "bgcolor": CARD,
        "bordercolor": RED,
        "font": {"color": WHITE, "size": 12},
    },
}

REGIME_COLORS = {
    "accumulation":   "#e63946",  # red — blood in the streets
    "early_bull":     "#22c55e",  # green — recovery
    "bull_expansion": "#f5f5f5",  # white — euphoria
    "late_bull":      "#f59e0b",  # gold — caution
    "blow_off":       "#dc143c",  # crimson — danger
    "distribution":   "#f59e0b",  # gold — warning
    "early_bear":     "#ef4444",  # red — decline
    "capitulation":   "#b71c1c",  # dark red — extreme fear
    "recovery":       "#888888",  # silver — uncertain
    "sideways":       "#666666",  # gray — neutral
}


def _apply(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply luxury layout + height to a figure."""

    fig.update_layout(**DARK_LAYOUT)
    fig.update_layout(height=height)
    return fig


def price_chart_with_signals(
    prices: pd.DataFrame,
    buy_signals: pd.DataFrame | None = None,
    sell_signals: pd.DataFrame | None = None,
    regimes: pd.Series | None = None,
) -> go.Figure:
    """ETH price chart with buy/sell markers and regime shading."""

    close = prices["close"] if isinstance(prices, pd.DataFrame) and "close" in prices else pd.Series(prices)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=close.index, y=close, name="ETH Close",
        line={"color": WHITE, "width": 1.5},
        fill="tozeroy", fillcolor="rgba(230,57,70,0.04)",
    ))
    if buy_signals is not None and len(buy_signals):
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals["price"] if "price" in buy_signals else buy_signals.iloc[:, 0],
            mode="markers", name="Buy",
            marker={"color": GREEN, "symbol": "triangle-up", "size": 10, "line": {"color": WHITE, "width": 1}},
        ))
    if sell_signals is not None and len(sell_signals):
        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals["price"] if "price" in sell_signals else sell_signals.iloc[:, 0],
            mode="markers", name="Sell",
            marker={"color": RED, "symbol": "triangle-down", "size": 10, "line": {"color": WHITE, "width": 1}},
        ))
    if regimes is not None and len(regimes):
        for regime_val, color in REGIME_COLORS.items():
            mask = regimes == regime_val
            if mask.any():
                idxs = mask[mask].index
                for idx in idxs:
                    fig.add_vrect(x0=idx, x1=idx + pd.Timedelta(days=1), fillcolor=color, opacity=0.04, layer="below", line_width=0)
    title_suffix = f" — Latest: {regimes.iloc[-1]}" if regimes is not None and len(regimes) else ""
    fig.update_layout(title=f"ETH / USD{title_suffix}")
    return _apply(fig, 500)


def equity_curve_chart(equity: pd.Series, benchmark_equity: pd.Series | None = None, benchmark_name: str = "Buy & Hold") -> go.Figure:
    """Strategy vs benchmark equity curve."""

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity, name="Strategy",
        line={"color": RED, "width": 2.5},
        fill="tozeroy", fillcolor="rgba(230,57,70,0.06)",
    ))
    if benchmark_equity is not None:
        fig.add_trace(go.Scatter(
            x=benchmark_equity.index, y=benchmark_equity, name=benchmark_name,
            line={"color": GRAY, "width": 1.5, "dash": "dash"},
        ))
    fig.update_layout(title="Portfolio Equity Curve", yaxis_title="USD")
    return _apply(fig, 450)


def drawdown_chart(equity: pd.Series) -> go.Figure:
    """Underwater drawdown plot."""

    dd = equity / equity.cummax() - 1
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dd.index, y=dd * 100,
        fill="tozeroy", name="Drawdown",
        line={"color": RED, "width": 0.5},
        fillcolor="rgba(230,57,70,0.25)",
    ))
    fig.update_layout(title="Drawdown from Peak", yaxis_title="Drawdown %")
    return _apply(fig, 350)


def exposure_chart(cash: pd.Series, eth_value: pd.Series) -> go.Figure:
    """Cash vs ETH exposure stacked area."""

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cash.index, y=cash, stackgroup="one", name="Cash",
        line={"color": GRAY, "width": 0},
        fillcolor="rgba(102,102,102,0.3)",
    ))
    fig.add_trace(go.Scatter(
        x=eth_value.index, y=eth_value, stackgroup="one", name="ETH",
        line={"color": RED, "width": 0},
        fillcolor="rgba(230,57,70,0.3)",
    ))
    fig.update_layout(title="Cash vs ETH Exposure", yaxis_title="USD")
    return _apply(fig, 350)


def signal_confidence_chart(scores: pd.Series) -> go.Figure:
    """Signal confidence 0-100 over time with colored bands."""

    fig = go.Figure()
    bands = [
        (0, 20, "rgba(230,57,70,0.12)"),
        (20, 41, "rgba(230,57,70,0.06)"),
        (41, 60, "rgba(102,102,102,0.04)"),
        (60, 75, "rgba(34,197,94,0.06)"),
        (75, 90, "rgba(34,197,94,0.10)"),
        (90, 101, "rgba(34,197,94,0.15)"),
    ]
    for lo, hi, color in bands:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=color, layer="below", line_width=0)
    fig.add_trace(go.Scatter(
        x=scores.index, y=scores, name="Signal Score",
        line={"color": WHITE, "width": 1.5},
    ))
    fig.update_layout(title="Signal Confidence Score (0–100)", yaxis={"range": [0, 100]})
    return _apply(fig, 400)


def rolling_sharpe_chart(returns: pd.Series, window: int = 252) -> go.Figure:
    """Rolling annualized Sharpe ratio."""

    sharpe = returns.rolling(window, min_periods=max(window // 2, 20)).mean() / returns.rolling(window, min_periods=max(window // 2, 20)).std() * (365**0.5)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sharpe.index, y=sharpe, name=f"Rolling Sharpe ({window}d)",
        line={"color": RED, "width": 1.5},
        fill="tozeroy", fillcolor="rgba(230,57,70,0.06)",
    ))
    fig.add_hline(y=0, line_color=GRAY, line_dash="dash")
    fig.update_layout(title=f"Rolling Sharpe Ratio ({window}-day)", yaxis_title="Sharpe")
    return _apply(fig, 350)


def rolling_volatility_chart(returns: pd.Series, window: int = 21) -> go.Figure:
    """Rolling annualized volatility."""

    vol = returns.rolling(window, min_periods=max(window // 2, 10)).std() * (365**0.5)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=vol.index, y=vol * 100, name=f"Rolling Vol ({window}d)",
        line={"color": GOLD, "width": 1.5},
        fill="tozeroy", fillcolor="rgba(245,158,11,0.06)",
    ))
    fig.update_layout(title=f"Rolling Annualized Volatility ({window}-day)", yaxis_title="Volatility %")
    return _apply(fig, 350)


def regime_distribution_chart(regimes: pd.Series) -> go.Figure:
    """Bar chart of regime distribution."""

    counts = regimes.value_counts()
    colors = [REGIME_COLORS.get(r, GRAY) for r in counts.index]
    fig = go.Figure(go.Bar(
        x=counts.index, y=counts.values,
        marker_color=colors,
        marker_line_color=WHITE, marker_line_width=0.5,
    ))
    fig.update_layout(title="Regime Distribution", xaxis_title="Regime", yaxis_title="Days")
    return _apply(fig, 350)


def regime_timeline_chart(regimes: pd.Series) -> go.Figure:
    """Regime classification over time as colored scatter."""

    fig = go.Figure()
    for regime_val, color in REGIME_COLORS.items():
        mask = regimes == regime_val
        if mask.any():
            subset = regimes[mask]
            fig.add_trace(go.Scatter(
                x=subset.index, y=[regime_val] * len(subset),
                mode="markers", name=regime_val,
                marker={"color": color, "size": 3},
            ))
    fig.update_layout(title="Regime Timeline", yaxis={"categoryorder": "array", "categoryarray": list(REGIME_COLORS.keys())})
    return _apply(fig, 400)


def monte_carlo_chart(percentiles: dict) -> go.Figure:
    """Monte Carlo percentile bar chart."""

    fig = go.Figure()
    if "p10" in percentiles:
        vals = [percentiles["p10"], percentiles["p25"], percentiles["p50"], percentiles["p75"], percentiles["p90"]]
        colors = [RED_DARK, RED, GRAY, GREEN, GREEN]
        fig.add_trace(go.Bar(
            x=["P10", "P25", "P50", "P75", "P90"], y=vals,
            marker_color=colors,
            marker_line_color=WHITE, marker_line_width=0.5,
        ))
    fig.update_layout(title="Monte Carlo: Outcome by Percentile", yaxis_title="Multiple (1x = breakeven)")
    return _apply(fig, 350)


def strategy_comparison_chart(results: dict) -> go.Figure:
    """Bar chart comparing strategy Sharpe ratios."""

    names = list(results.keys())
    sharpe_vals = [results[n].get("sharpe_ratio", 0) for n in names]
    fig = go.Figure(go.Bar(
        x=names, y=sharpe_vals,
        marker_color=[RED if n == "Signal Driven" else GRAY for n in names],
        marker_line_color=WHITE, marker_line_width=0.5,
    ))
    fig.update_layout(title="Sharpe Ratio Comparison", yaxis_title="Sharpe")
    return _apply(fig, 350)