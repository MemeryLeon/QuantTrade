from __future__ import annotations

from fastapi import Request

from app.application.backtests import BacktestApplicationService


def get_backtest_service(request: Request) -> BacktestApplicationService:
    service = request.app.state.backtest_service
    if not isinstance(service, BacktestApplicationService):
        raise RuntimeError("backtest application service is not configured")
    return service
