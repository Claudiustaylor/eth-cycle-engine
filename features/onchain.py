"""Optional on-chain features."""

from __future__ import annotations

import pandas as pd

from features.utils import rolling_percentile


def exchange_inflow_percentile(inflow: pd.Series | None, window: int = 252) -> pd.Series | None:
    """Return inflow percentile or None when unavailable."""

    return None if inflow is None else rolling_percentile(inflow, window)


def exchange_outflow_percentile(outflow: pd.Series | None, window: int = 252) -> pd.Series | None:
    """Return outflow percentile or None when unavailable."""

    return None if outflow is None else rolling_percentile(outflow, window)


def mvrv_percentile(mvrv: pd.Series | None, window: int = 252) -> pd.Series | None:
    """Return MVRV percentile or None when unavailable."""

    return None if mvrv is None else rolling_percentile(mvrv, window)


def realized_price_deviation(
    price: pd.Series | None, realized_price: pd.Series | None
) -> pd.Series | None:
    """Return price deviation from realized price or None when unavailable."""

    if price is None or realized_price is None:
        return None
    return price / realized_price - 1.0


def network_activity_acceleration(
    active_addresses: pd.Series | None, window: int = 14
) -> pd.Series | None:
    """Return active-address acceleration or None when unavailable."""

    return None if active_addresses is None else active_addresses.pct_change(window)
