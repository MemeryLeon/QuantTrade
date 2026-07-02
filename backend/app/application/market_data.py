from __future__ import annotations

from datetime import date

from app.domains.market import (
    BarsRequest,
    BarsResult,
    DataSourceHealth,
    IDataProvider,
    IDataProviderHealth,
    Instrument,
    Quote,
    TradingCalendar,
)


class MarketDataApplicationService:
    def __init__(self, provider: IDataProvider, health: IDataProviderHealth) -> None:
        self._provider = provider
        self._health = health

    async def search_instruments(self, query: str) -> tuple[Instrument, ...]:
        return tuple(await self._provider.search_instruments(query))

    async def get_bars(self, request: BarsRequest) -> BarsResult:
        return await self._provider.get_bars(request)

    async def get_quote(self, instrument_id: str) -> Quote:
        return await self._provider.get_quote(instrument_id)

    async def get_calendar(self, market: str, start: date, end: date) -> TradingCalendar:
        return await self._provider.get_calendar(market, start, end)

    async def get_health(self, provider: str) -> DataSourceHealth:
        return await self._health.get_health(provider)

