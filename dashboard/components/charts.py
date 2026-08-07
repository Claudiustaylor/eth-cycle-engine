"""Reusable Plotly charts."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def price_chart_with_signals(prices: pd.DataFrame | pd.Series, buy_signals: pd.Series | None = None, sell_signals: pd.Series | None = None, regimes: pd.Series | None = None) -> go.Figure:
    """Create price chart with optional signal markers and regime shading."""

    fig = go.Figure()
    close = prices["close"] if isinstance(prices, pd.DataFrame) and "close" in prices else pd.Series(prices)
    fig.add_trace(go.Scatter(x=close.index, y=close, name="ETH close"))
    if buy_signals is not None:
        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals, mode="markers", name="Buys", marker={"color": "green", "symbol": "triangle-up"}))
    if sell_signals is not None:
        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals, mode="markers", name="Sells", marker={"color": "red", "symbol": "triangle-down"}))
    if regimes is not None and len(regimes):
        fig.update_layout(title=f"ETH Price by Regime - latest: {regimes.iloc[-1]}")
    return fig


def equity_curve_chart(equity: pd.Series, benchmark_equity: pd.Series | None = None) -> go.Figure:
    """Create strategy versus benchmark equity chart."""

    fig = go.Figure(go.Scatter(x=equity.index, y=equity, name="Strategy"))
    if benchmark_equity is not None:
        fig.add_trace(go.Scatter(x=benchmark_equity.index, y=benchmark_equity, name="Benchmark"))
    return fig


def drawdown_chart(equity: pd.Series) -> go.Figure:
    """Create underwater drawdown chart."""

    dd = equity / equity.cummax() - 1
    return go.Figure(go.Scatter(x=dd.index, y=dd, fill="tozeroy", name="Drawdown"))


def exposure_chart(cash: pd.Series, eth_value: pd.Series) -> go.Figure:
    """Create cash versus ETH exposure chart."""

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cash.index, y=cash, stackgroup="one", name="Cash"))
    fig.add_trace(go.Scatter(x=eth_value.index, y=eth_value, stackgroup="one", name="ETH"))
    return fig


def signal_confidence_chart(scores: pd.Series) -> go.Figure:
    """Create signal confidence chart with bands."""

    fig = go.Figure(go.Scatter(x=scores.index, y=scores, name="Score"))
    fig.update_yaxes(range=[0, 100])
    return fig


def rolling_sharpe_chart(returns: pd.Series, window: int = 252) -> go.Figure:
    """Create rolling Sharpe chart."""

    sharpe = returns.rolling(window, min_periods=window).mean() / returns.rolling(window, min_periods=window).std() * (365**0.5)
    return go.Figure(go.Scatter(x=sharpe.index, y=sharpe, name="Rolling Sharpe"))


def rolling_volatility_chart(returns: pd.Series, window: int = 21) -> go.Figure:
    """Create rolling volatility chart."""

    vol = returns.rolling(window, min_periods=window).std() * (365**0.5)
    return go.Figure(go.Scatter(x=vol.index, y=vol, name="Rolling Volatility"))
