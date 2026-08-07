"""Typed data schemas for market, macro, on-chain, derivatives, and staking data."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class OHLCVBar:
    """Single OHLCV market bar."""

    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MacroData:
    """Daily macro market data."""

    date: pd.Timestamp
    fed_funds_rate: float
    cpi_yoy: float
    dxy: float
    treasury_10y: float
    treasury_2y: float
    sp500: float
    nasdaq: float


@dataclass(frozen=True)
class OnChainData:
    """Daily optional on-chain data."""

    date: pd.Timestamp
    active_addresses: float
    tx_volume: float
    gas_fees: float
    network_revenue: float
    exchange_inflow: float
    exchange_outflow: float
    exchange_reserve: float
    mvrv: float
    realized_price: float
    eth_supply: float


@dataclass(frozen=True)
class DerivativesData:
    """Daily optional derivatives market data."""

    date: pd.Timestamp
    funding_rate: float
    open_interest: float
    liquidations_long: float
    liquidations_short: float


@dataclass(frozen=True)
class StakingData:
    """Daily optional staking data."""

    date: pd.Timestamp
    staking_yield: float
    total_staked: float
    staking_ratio: float


@dataclass(frozen=True)
class DataSet:
    """Container returned by the ingestion layer."""

    eth_ohlcv: pd.DataFrame | None = None
    btc_ohlcv: pd.DataFrame | None = None
    macro: pd.DataFrame | None = None
    eth_btc_ratio: pd.DataFrame | None = None
    onchain: pd.DataFrame | None = None
    derivatives: pd.DataFrame | None = None
    staking: pd.DataFrame | None = None
