"""Data ingestion layer using real free data and explicit unavailable fallbacks."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from data.schemas import DataSet
from data.storage import load_parquet, save_parquet

logger = logging.getLogger(__name__)


class DataIngestion:
    """Fetch and cache market data, while never fabricating unavailable sources."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        data_cfg = config.get("data", {})
        self.sources = data_cfg.get("sources", {})
        self.cache = data_cfg.get("cache", {})
        self.base_path = self.cache.get("path", "data/parquet/")
        self.max_age_hours = float(self.cache.get("max_age_hours", 24))

    def _cache_fresh(self, name: str) -> bool:
        path = Path(self.base_path) / name
        if not path.exists():
            return False
        newest = max((p.stat().st_mtime for p in path.rglob("*.parquet")), default=0)
        age = datetime.now(UTC) - datetime.fromtimestamp(newest, tz=UTC)
        return age <= timedelta(hours=self.max_age_hours)

    def _from_cache(self, name: str) -> pd.DataFrame | None:
        if self._cache_fresh(name):
            return load_parquet(name, self.base_path)
        return None

    def _download_yfinance(
        self, ticker: str, start: str, end: str, interval: str = "1d"
    ) -> pd.DataFrame | None:
        try:
            import yfinance as yf

            if interval == "1h":
                # yfinance hourly: use period param (max 730d) instead of start/end
                raw = yf.download(ticker, period="60d", interval="1h", progress=False)
            else:
                raw = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
            if raw.empty:
                logger.warning("No yfinance rows returned for %s", ticker)
                return None
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            df = raw.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            )
            return df[[c for c in ["open", "high", "low", "close", "adj_close", "volume"] if c in df]]
        except Exception as exc:  # pragma: no cover - network/provider defensive path
            logger.warning("Failed to fetch %s from yfinance: %s", ticker, exc)
            return None

    def fetch_eth_ohlcv(self, start: str, end: str, interval: str = "1d") -> pd.DataFrame | None:
        """Fetch ETH-USD OHLCV from yfinance and cache to Parquet."""

        name = f"eth_ohlcv_{interval}"
        cached = self._from_cache(name)
        if cached is not None:
            return cached
        df = self._download_yfinance("ETH-USD", start, end, interval)
        if df is not None:
            save_parquet(df, name, self.base_path)
        return df

    def fetch_btc_ohlcv(self, start: str, end: str, interval: str = "1d") -> pd.DataFrame | None:
        """Fetch BTC-USD OHLCV from yfinance and cache to Parquet."""

        name = f"btc_ohlcv_{interval}"
        cached = self._from_cache(name)
        if cached is not None:
            return cached
        df = self._download_yfinance("BTC-USD", start, end, interval)
        if df is not None:
            save_parquet(df, name, self.base_path)
        return df

    def fetch_macro(self, start: str, end: str) -> pd.DataFrame | None:
        """Fetch free macro proxies from yfinance; CPI and Fed Funds remain unavailable."""

        cached = self._from_cache("macro")
        if cached is not None:
            return cached
        try:
            tickers = {
                "irx": "^IRX",        # 13-week T-bill (proxy for fed funds)
                "tnx": "^TNX",        # 10-year treasury yield
                "fvx": "^FVX",        # 5-year treasury yield
                "sp500": "^GSPC",     # S&P 500
                "nasdaq": "^IXIC",    # Nasdaq
                "dxy": "DX-Y.NYB",    # Dollar Index
                "vix": "^VIX",        # Volatility Index
                "gold": "GC=F",       # Gold futures (safe-haven proxy)
            }
            frames: list[pd.Series] = []
            for name, ticker in tickers.items():
                df = self._download_yfinance(ticker, start, end)
                if df is not None and "close" in df:
                    frames.append(df["close"].rename(name))
            if not frames:
                return None
            macro = pd.concat(frames, axis=1).ffill()
            macro["treasury_2y"] = macro.get("fvx")  # 5-yr as 2-yr proxy (closest free)
            macro["treasury_10y"] = macro.get("tnx")
            macro["fed_funds_rate"] = macro.get("irx")  # T-bill as fed funds proxy
            macro["cpi_yoy"] = pd.NA  # Still requires FRED — no free proxy
            logger.warning("FRED API key not configured; CPI year-over-year remains unavailable.")
            save_parquet(macro, "macro", self.base_path)
            return macro
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to fetch macro data: %s", exc)
            return None

    def fetch_eth_btc_ratio(self, start: str, end: str) -> pd.DataFrame | None:
        """Fetch or compute ETH/BTC close ratio from real ETH and BTC prices."""

        cached = self._from_cache("eth_btc_ratio")
        if cached is not None:
            return cached
        eth = self.fetch_eth_ohlcv(start, end)
        btc = self.fetch_btc_ohlcv(start, end)
        if eth is None or btc is None:
            return None
        ratio = (eth["close"] / btc["close"]).rename("eth_btc_ratio").to_frame()
        save_parquet(ratio, "eth_btc_ratio", self.base_path)
        return ratio

    def fetch_onchain(self, start: str, end: str) -> pd.DataFrame | None:
        """Return None when no paid on-chain provider is configured."""

        _ = (start, end)
        logger.warning("On-chain provider unavailable; returning None without fabricated data.")
        return None

    def fetch_derivatives(self, start: str, end: str) -> pd.DataFrame | None:
        """Return None when no paid derivatives provider is configured."""

        _ = (start, end)
        logger.warning("Derivatives provider unavailable; returning None without fabricated data.")
        return None

    def fetch_staking(self, start: str, end: str) -> pd.DataFrame | None:
        """Return configured staking data only when explicitly enabled as placeholder config data."""

        src = self.sources.get("staking", {})
        if not src.get("enabled", False):
            logger.warning("Staking source disabled; returning None.")
            return None
        if src.get("provider") != "config":
            logger.warning("Staking provider unavailable; returning None without fabricated data.")
            return None
        dates = pd.date_range(start, end, freq="D")
        df = pd.DataFrame(index=dates, data={"staking_yield": float(src.get("default_yield", 0.03))})
        df["total_staked"] = pd.NA
        df["staking_ratio"] = pd.NA
        save_parquet(df, "staking", self.base_path)
        return df

    def fetch_all(self, start: str, end: str) -> DataSet:
        """Fetch all enabled data sources and return a DataSet."""

        return DataSet(
            eth_ohlcv=self.fetch_eth_ohlcv(start, end)
            if self.sources.get("eth_ohlcv", {}).get("enabled", True)
            else None,
            btc_ohlcv=self.fetch_btc_ohlcv(start, end)
            if self.sources.get("btc_ohlcv", {}).get("enabled", True)
            else None,
            macro=self.fetch_macro(start, end)
            if self.sources.get("macro", {}).get("enabled", True)
            else None,
            eth_btc_ratio=self.fetch_eth_btc_ratio(start, end),
            onchain=self.fetch_onchain(start, end)
            if self.sources.get("onchain", {}).get("enabled", False)
            else None,
            derivatives=self.fetch_derivatives(start, end)
            if self.sources.get("derivatives", {}).get("enabled", False)
            else None,
            staking=self.fetch_staking(start, end)
            if self.sources.get("staking", {}).get("enabled", False)
            else None,
        )
