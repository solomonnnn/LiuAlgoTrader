"""Base Class for Strategies"""
from datetime import datetime
from typing import Dict

import alpaca_trade_api as tradeapi
from pandas import DataFrame as df

from common import config, trading_data
from common.trading_data import open_orders
from models.algo_run import AlgoRun


class Strategy:
    def __init__(self, name: str, trading_api: tradeapi, data_api: tradeapi):
        self.name = name
        self.trading_api = trading_api
        self.data_api = data_api
        self.algo_run = AlgoRun(strategy_name=self.name)

    async def create(self):
        await self.algo_run.save(pool=trading_data.db_conn_pool)

    async def run(
        self, symbol: str, position: int, minute_history: df, now: datetime
    ) -> bool:
        return False

    async def is_sell_time(self, now: datetime):
        return (
            True
            if (
                (now - config.market_open).seconds // 60
                >= config.market_cool_down_minutes
                or config.bypass_market_schedule
            )
            and (config.market_close - now).seconds // 60 > 15
            else False
        )

    async def is_buy_time(self, now: datetime):
        return (
            True
            if config.trade_buy_window
            > (now - config.market_open).seconds // 60
            > config.market_cool_down_minutes
            or config.bypass_market_schedule
            else False
        )

    async def buy_callback(self, symbol: str, price: float, qty: int) -> None:
        pass

    async def sell_callback(self, symbol: str, price: float, qty: int) -> None:
        pass

    async def execute_buy_limit(
        self, symbol: str, price: float, qty: int, indicators: Dict
    ) -> None:
        o = self.trading_api.submit_order(
            symbol=symbol,
            qty=str(qty),
            side="buy",
            type="limit",
            time_in_force="day",
            limit_price=str(price),
        )
        open_orders[o.client_order_id] = (o, "buy", indicators, self)

    async def execute_sell_limit(
        self, symbol: str, price: float, qty: int, indicators: Dict
    ) -> None:
        o = self.trading_api.submit_order(
            symbol=symbol,
            qty=str(qty),
            side="sell",
            type="limit",
            time_in_force="day",
            limit_price=str(price),
        )
        open_orders[o.client_order_id] = (o, "sell", indicators, self)

    async def execute_buy_market(
        self, symbol: str, qty: int, indicators: Dict
    ) -> None:
        raise Exception("Not Implemented Yet")

    async def execute_sell_market(
        self, symbol: str, qty: int, indicators: Dict
    ) -> None:
        o = self.trading_api.submit_order(
            symbol=symbol,
            qty=str(qty),
            side="sell",
            type="market",
            time_in_force="day",
        )
        open_orders[o.client_order_id] = (o, "sell", indicators, self)
