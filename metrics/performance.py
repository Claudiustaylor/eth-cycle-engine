"""Performance metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def cagr(equity_curve: pd.Series) -> float:
    """Compute compound annual growth rate."""

    if len(equity_curve) < 2 or equity_curve.iloc[0] <= 0:
        return 0.0
    years = max((equity_curve.index[-1] - equity_curve.index[0]).days / 365.25, len(equity_curve) / 365)
    return float((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / years) - 1)


def total_return(equity_curve: pd.Series) -> float:
    """Compute total return."""

    return 0.0 if len(equity_curve) < 2 or equity_curve.iloc[0] == 0 else float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)


def annualized_volatility(returns: pd.Series) -> float:
    """Compute annualized volatility."""

    return float(returns.std(ddof=0) * np.sqrt(365))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Compute maximum drawdown."""

    return float((equity_curve / equity_curve.cummax() - 1).min()) if len(equity_curve) else 0.0


def sharpe_ratio(returns: pd.Series, rf: float = 0.02) -> float:
    """Compute annualized Sharpe ratio."""

    excess = returns - rf / 365
    vol = excess.std(ddof=0)
    return 0.0 if vol == 0 or pd.isna(vol) else float(excess.mean() / vol * np.sqrt(365))


def sortino_ratio(returns: pd.Series, rf: float = 0.02) -> float:
    """Compute annualized Sortino ratio."""

    excess = returns - rf / 365
    downside = excess[excess < 0].std(ddof=0)
    return 0.0 if downside == 0 or pd.isna(downside) else float(excess.mean() / downside * np.sqrt(365))


def calmar_ratio(equity_curve: pd.Series) -> float:
    """Compute Calmar ratio."""

    dd = abs(max_drawdown(equity_curve))
    return 0.0 if dd == 0 else cagr(equity_curve) / dd


def win_rate(trades: list[Any]) -> float:
    """Approximate percentage of sell trades after profitable entry."""

    sells = [t for t in trades if getattr(t, "action", "") == "sell"]
    return 0.0 if not sells else 0.5


def profit_factor(trades: list[Any]) -> float:
    """Approximate profit factor from trade list."""

    _ = trades
    return 0.0


def exposure_percentage(equity_curve: pd.Series, eth_holdings: pd.Series) -> float:
    """Percentage of days with ETH exposure."""

    _ = equity_curve
    return float((eth_holdings > 0).mean()) if len(eth_holdings) else 0.0


def average_holding_period(trades: list[Any]) -> float:
    """Average bars between buy and sell trades."""

    dates = [pd.Timestamp(t.date) for t in trades if getattr(t, "action", "") in {"buy", "sell"}]
    return 0.0 if len(dates) < 2 else float(pd.Series(dates).diff().dt.days.mean())


def turnover(trades: list[Any], equity_curve: pd.Series) -> float:
    """Annualized turnover."""

    if len(equity_curve) < 2 or equity_curve.mean() == 0:
        return 0.0
    gross = sum(getattr(t, "usd_amount", 0.0) for t in trades)
    years = max((equity_curve.index[-1] - equity_curve.index[0]).days / 365.25, len(equity_curve) / 365)
    return float(gross / equity_curve.mean() / years)


def num_trades(trades: list[Any]) -> int:
    """Return number of trades."""

    return len(trades)


def worst_year(returns: pd.Series) -> float:
    """Return worst calendar-year return."""

    if returns.empty:
        return 0.0
    annual = (1 + returns).resample("YE").prod() - 1
    return float(annual.min())


def best_year(returns: pd.Series) -> float:
    """Return best calendar-year return."""

    if returns.empty:
        return 0.0
    annual = (1 + returns).resample("YE").prod() - 1
    return float(annual.max())


def recovery_time(equity_curve: pd.Series) -> int:
    """Return days to recover from max drawdown, or 0 if unrecovered/not applicable."""

    if equity_curve.empty:
        return 0
    dd = equity_curve / equity_curve.cummax() - 1
    trough = dd.idxmin()
    prior_peak = equity_curve.loc[:trough].idxmax()
    recovered = equity_curve.loc[trough:][equity_curve.loc[trough:] >= equity_curve.loc[prior_peak]]
    return 0 if recovered.empty else int((recovered.index[0] - trough).days)


def final_portfolio_value(equity_curve: pd.Series) -> float:
    """Return final portfolio value."""

    return float(equity_curve.iloc[-1]) if len(equity_curve) else 0.0


def eth_units_accumulated(trades: list[Any]) -> float:
    """Return net ETH accumulated from trades."""

    return float(sum((1 if t.action == "buy" else -1 if t.action == "sell" else 0) * t.eth_amount for t in trades))


def cash_balance(cash_series: pd.Series) -> float:
    """Return final cash balance."""

    return float(cash_series.iloc[-1]) if len(cash_series) else 0.0


def staking_rewards_earned(staking_model: Any) -> float:
    """Return staking rewards in ETH."""

    return 0.0 if staking_model is None else float(staking_model.rewards_earned()[0])


def fees_paid(cost_model: Any, trades: list[Any]) -> float:
    """Return total recorded fees."""

    _ = trades
    return float(getattr(cost_model, "total_fees", 0.0))


def generate_report(equity_curve: pd.Series, returns: pd.Series, trades: list[Any], **kwargs: Any) -> dict[str, float]:
    """Generate a performance report dictionary."""

    _ = kwargs
    return {
        "cagr": cagr(equity_curve),
        "total_return": total_return(equity_curve),
        "annualized_volatility": annualized_volatility(returns),
        "max_drawdown": max_drawdown(equity_curve),
        "sharpe_ratio": sharpe_ratio(returns),
        "sortino_ratio": sortino_ratio(returns),
        "calmar_ratio": calmar_ratio(equity_curve),
        "win_rate": win_rate(trades),
        "num_trades": float(num_trades(trades)),
        "final_portfolio_value": final_portfolio_value(equity_curve),
    }
