from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_market_data_service
from app.application.market_data import MarketDataApplicationService
from app.contracts.market import (
    BarResponse,
    BarsResponse,
    DataSourceHealthResponse,
    InstrumentResponse,
    InstrumentSearchResponse,
    TradingCalendarResponse,
)
from app.core.errors import ApiError
from app.domains.market import BarsRequest


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/instruments/search")
async def search_instruments(
    query: str = Query(min_length=1),
    service: MarketDataApplicationService = Depends(get_market_data_service),
) -> InstrumentSearchResponse:
    instruments = await service.search_instruments(query)
    return InstrumentSearchResponse(
        instruments=tuple(
            InstrumentResponse(
                instrument_id=instrument.instrument_id,
                symbol=instrument.symbol,
                name=instrument.name,
                market=instrument.market,
                exchange_timezone=instrument.exchange_timezone,
            )
            for instrument in instruments
        )
    )


@router.get("/bars")
async def get_bars(
    instrument_id: str,
    start: datetime,
    end: datetime,
    resolution: Literal["daily"] = "daily",
    adjustment: Literal["none", "qfq", "hfq"] = "none",
    service: MarketDataApplicationService = Depends(get_market_data_service),
) -> BarsResponse:
    try:
        result = await service.get_bars(
            BarsRequest(
                instrument_id=instrument_id,
                start=start,
                end=end,
                resolution=resolution,
                adjustment=adjustment,
            )
        )
    except ValueError as exc:
        raise ApiError(
            status_code=400,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"instrument_id": instrument_id},
        ) from exc
    return BarsResponse(
        instrument_id=result.instrument_id,
        provider="akshare",
        market="CN_A",
        currency="CNY",
        resolution=resolution,
        adjustment=adjustment,
        timezone="Asia/Shanghai",
        bars=tuple(
            BarResponse(
                observed_at=bar.observed_at,
                open_price=Decimal(bar.open_price),
                high_price=Decimal(bar.high_price),
                low_price=Decimal(bar.low_price),
                close_price=Decimal(bar.close_price),
                volume=bar.volume,
                quality_flags=bar.quality_flags,
            )
            for bar in result.bars
        ),
        as_of=result.as_of,
        is_delayed=result.is_delayed,
        stale_age_seconds=result.stale_age_seconds,
        quality_flags=result.quality_flags,
    )


@router.get("/calendar")
async def get_calendar(
    market: Literal["CN_A"] = "CN_A",
    start: date = Query(),
    end: date = Query(),
    service: MarketDataApplicationService = Depends(get_market_data_service),
) -> TradingCalendarResponse:
    calendar = await service.get_calendar(market, start, end)
    return TradingCalendarResponse(
        market=calendar.market,
        version=calendar.version,
        timezone=calendar.timezone,
        trading_days=calendar.trading_days,
    )


@router.get("/data-sources/{provider}/health")
async def get_data_source_health(
    provider: Literal["akshare"],
    service: MarketDataApplicationService = Depends(get_market_data_service),
) -> DataSourceHealthResponse:
    health = await service.get_health(provider)
    return DataSourceHealthResponse(
        provider=health.provider,
        status=health.status,
        checked_at=health.checked_at,
        consecutive_failures=health.consecutive_failures,
        last_success_at=health.last_success_at,
        last_error_code=health.last_error_code,
        stale_cache_available=health.stale_cache_available,
        stale_age_seconds=health.stale_age_seconds,
    )
