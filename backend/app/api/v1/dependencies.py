from __future__ import annotations

from fastapi import Request

from app.application.backtests import BacktestApplicationService
from app.application.market_data import MarketDataApplicationService


def get_backtest_service(request: Request) -> BacktestApplicationService:
    service = request.app.state.backtest_service
    if not isinstance(service, BacktestApplicationService):
        raise RuntimeError("backtest application service is not configured")
    return service


def get_market_data_service(request: Request) -> MarketDataApplicationService:
    service = request.app.state.market_data_service
    if not isinstance(service, MarketDataApplicationService):
        raise RuntimeError("market data application service is not configured")
    return service
