from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.domains.indicators import (
    IndicatorPoint,
    IndicatorResult,
    adx,
    bollinger_bands,
    ema,
    macd,
    rsi,
    sma,
)
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

    async def get_indicators(self, request: BarsRequest) -> IndicatorResult:
        bars_result = await self._provider.get_bars(request)
        bars = bars_result.bars
        closes = tuple(bar.close_price for bar in bars)
        highs = tuple(bar.high_price for bar in bars)
        lows = tuple(bar.low_price for bar in bars)
        sma_values = sma(closes, 20)
        ema_values = ema(closes, 20)
        macd_result = macd(closes)
        rsi_values = rsi(closes)
        bands = bollinger_bands(closes, multiplier=Decimal("2"))
        adx_values = adx(highs, lows, closes)

        points = tuple(
            IndicatorPoint(
                observed_at=bar.observed_at,
                sma=sma_value,
                ema=ema_value,
                macd=macd_value,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram,
                rsi=rsi_value,
                bollinger_middle=bollinger_middle,
                bollinger_upper=bollinger_upper,
                bollinger_lower=bollinger_lower,
                adx=adx_value,
            )
            for (
                bar,
                sma_value,
                ema_value,
                macd_value,
                macd_signal,
                macd_histogram,
                rsi_value,
                bollinger_middle,
                bollinger_upper,
                bollinger_lower,
                adx_value,
            ) in zip(
                bars,
                sma_values,
                ema_values,
                macd_result.macd,
                macd_result.signal,
                macd_result.histogram,
                rsi_values,
                bands.middle,
                bands.upper,
                bands.lower,
                adx_values,
                strict=True,
            )
        )
        return IndicatorResult(
            instrument_id=bars_result.instrument_id,
            points=points,
            as_of=bars_result.as_of,
            is_delayed=bars_result.is_delayed,
            stale_age_seconds=bars_result.stale_age_seconds,
            quality_flags=bars_result.quality_flags,
        )

    async def get_quote(self, instrument_id: str) -> Quote:
        return await self._provider.get_quote(instrument_id)

    async def get_calendar(self, market: str, start: date, end: date) -> TradingCalendar:
        return await self._provider.get_calendar(market, start, end)

    async def get_health(self, provider: str) -> DataSourceHealth:
        return await self._health.get_health(provider)
