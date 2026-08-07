"""Feature registry that combines configured feature groups."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from data.schemas import DataSet
from features import drawdown, macro, market_structure, momentum, volatility, volume
from features.trend import compute_ema_slope, compute_emas, ma_crossovers, price_vs_ma

logger = logging.getLogger(__name__)


class FeatureRegistry:
    """Compute all enabled features into a single aligned DataFrame."""

    def __init__(self, dataset: DataSet, config: dict[str, Any]) -> None:
        self.dataset = dataset
        self.config = config

    def compute(self) -> pd.DataFrame:
        """Return a feature DataFrame with skipped groups logged."""

        eth = self.dataset.eth_ohlcv
        if eth is None or eth.empty:
            raise ValueError("ETH OHLCV data is required")
        cfg = self.config.get("features", {})
        prices = eth["close"]
        out = eth.copy()
        out["returns"] = prices.pct_change()
        if cfg.get("trend", {}).get("enabled", True):
            periods = cfg.get("trend", {}).get("ema_periods", [20, 50, 100, 200])
            emas = compute_emas(prices, periods)
            out = out.join(emas)
            for p in periods:
                out[f"ema_{p}_slope"] = compute_ema_slope(out[f"ema_{p}"])
                out[f"price_vs_ema_{p}"] = price_vs_ma(prices, out[f"ema_{p}"])
            if {"ema_50", "ema_200"} <= set(out.columns):
                out["ema_50_200_cross"] = ma_crossovers(out["ema_50"], out["ema_200"])
        if cfg.get("momentum", {}).get("enabled", True):
            rsi_period = cfg.get("momentum", {}).get("rsi_period", 14)
            macd_cfg = cfg.get("momentum", {}).get("macd", [12, 26, 9])
            out["rsi"] = momentum.compute_rsi(prices, rsi_period)
            out = out.join(momentum.compute_macd(prices, *macd_cfg))
            out["roc_14"] = momentum.rate_of_change(prices, 14)
            out["momentum_percentile"] = momentum.momentum_percentile(prices, out["roc_14"])
            if self.dataset.btc_ohlcv is not None:
                out["rs_vs_btc"] = momentum.relative_strength_vs_btc(
                    prices, self.dataset.btc_ohlcv["close"].reindex(out.index).ffill()
                )
        if cfg.get("volatility", {}).get("enabled", True):
            rv_window = cfg.get("volatility", {}).get("rv_window", 21)
            out["atr"] = volatility.compute_atr(eth["high"], eth["low"], prices)
            out["realized_vol"] = volatility.realized_volatility(out["returns"], rv_window)
            out["bb_width"] = volatility.bollinger_band_width(prices)
            out["vol_percentile"] = volatility.volatility_percentile(out["realized_vol"])
            out["vol_expansion"] = volatility.volatility_expansion(
                volatility.realized_volatility(out["returns"], 7),
                volatility.realized_volatility(out["returns"], 63),
            )
        if cfg.get("drawdown", {}).get("enabled", True):
            cycle_window = cfg.get("drawdown", {}).get("cycle_window", 252)
            out["drawdown_ath"] = drawdown.drawdown_from_ath(prices)
            out["drawdown_cycle"] = drawdown.drawdown_from_cycle_high(prices, cycle_window)
            out["drawdown_30d"] = drawdown.drawdown_30d(prices)
            out["drawdown_90d"] = drawdown.drawdown_90d(prices)
            out["max_trailing_drawdown"] = drawdown.max_trailing_drawdown(prices, cycle_window)
        if cfg.get("volume", {}).get("enabled", True):
            out["volume_vs_ma"] = volume.volume_vs_ma(eth["volume"])
            out["volume_acceleration"] = volume.volume_acceleration(eth["volume"])
            out["price_volume_divergence"] = volume.price_volume_divergence(prices, eth["volume"])
        if cfg.get("market_structure", {}).get("enabled", True):
            w = cfg.get("market_structure", {}).get("structure_window", 20)
            out = out.join(market_structure.higher_highs_higher_lows(prices, w))
            out = out.join(market_structure.lower_highs_lower_lows(prices, w))
            out["distance_from_local_high"] = market_structure.distance_from_local_high(prices, w)
            out["distance_from_local_low"] = market_structure.distance_from_local_low(prices, w)
            out["breakout"] = market_structure.breakout_detection(prices, w)
            out["failed_breakout"] = market_structure.failed_breakout_detection(prices, w)
        if cfg.get("macro", {}).get("enabled", True) and self.dataset.macro is not None:
            m = self.dataset.macro.reindex(out.index).ffill()
            vix = m.get("vix", None)
            if {"sp500", "dxy"} <= set(m.columns):
                out["risk_on_off"] = macro.risk_on_risk_off(m["sp500"], m["dxy"], vix)
                out["dollar_trend"] = macro.dollar_strength_trend(m["dxy"])
                out["equity_trend"] = macro.equity_market_trend(m["sp500"])
            if "treasury_2y" in m:
                out["rate_direction"] = macro.rate_direction(pd.to_numeric(m["treasury_2y"], errors="coerce"))
            if "treasury_10y" in m and not pd.isna(m["treasury_10y"]).all():
                out["rate_direction_10y"] = macro.rate_direction_10y(m["treasury_10y"])
            if "gold" in m:
                out["gold_trend"] = macro.dollar_strength_trend(m["gold"]).rename("gold_trend")  # reuse pct_change
            if "nasdaq" in m:
                out["nasdaq_trend"] = macro.equity_market_trend(m["nasdaq"])
        else:
            logger.info("Macro features skipped; macro data unavailable or disabled.")
        if cfg.get("derivatives", {}).get("enabled", False) and self.dataset.derivatives is None:
            logger.warning("Derivative features skipped; data unavailable.")
        if cfg.get("onchain", {}).get("enabled", False) and self.dataset.onchain is None:
            logger.warning("On-chain features skipped; data unavailable.")
        return out
