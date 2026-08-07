"""Transaction cost model."""

from __future__ import annotations

from typing import Any


class TransactionCosts:
    """Apply trading, spread, slippage, and staking costs."""

    def __init__(self, config: dict[str, Any]) -> None:
        cfg = config.get("transaction_costs", {})
        self.trading_fee_pct = float(cfg.get("trading_fee_pct", 0.001))
        self.spread_pct = float(cfg.get("spread_pct", 0.0005))
        self.slippage_pct = float(cfg.get("slippage_pct", 0.001))
        self.staking_fee_pct = float(cfg.get("staking_fee_pct", 0.0))
        self.withdrawal_fee = float(cfg.get("withdrawal_fee", 0.0))
        self.total_fees = 0.0

    def buy_cost(self, usd_amount: float) -> float:
        """Return total USD cost for a buy."""

        cost = usd_amount * (self.trading_fee_pct + self.spread_pct + self.slippage_pct)
        self.total_fees += cost
        return cost

    def sell_cost(self, usd_amount: float) -> float:
        """Return net USD proceeds after sell costs."""

        cost = usd_amount * (self.trading_fee_pct + self.spread_pct + self.slippage_pct)
        self.total_fees += cost
        return usd_amount - cost

    def staking_fee(self, eth_amount: float, eth_price: float) -> float:
        """Return staking fee in USD."""

        fee = eth_amount * eth_price * self.staking_fee_pct + self.withdrawal_fee
        self.total_fees += fee
        return fee
