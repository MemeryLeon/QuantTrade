from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


class DataSourceStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"


class QualityFlag(StrEnum):
    MISSING_BARS = "MISSING_BARS"
    DUPLICATE_BARS = "DUPLICATE_BARS"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    STALE_CACHE = "STALE_CACHE"
    PROVIDER_DEGRADED = "PROVIDER_DEGRADED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    ADJUSTMENT_FACTOR_MISSING = "ADJUSTMENT_FACTOR_MISSING"
    CALENDAR_MISMATCH = "CALENDAR_MISMATCH"
    TIMEZONE_AMBIGUOUS = "TIMEZONE_AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class Instrument:
    instrument_id: str
    symbol: str
    name: str
    market: str
    exchange_timezone: str


@dataclass(frozen=True, slots=True)
class BarsRequest:
    instrument_id: str
    start: datetime
    end: datetime
    resolution: str
    adjustment: str


@dataclass(frozen=True, slots=True)
class Bar:
    observed_at: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    quality_flags: tuple[QualityFlag, ...]


@dataclass(frozen=True, slots=True)
class BarsResult:
    instrument_id: str
    bars: tuple[Bar, ...]
    as_of: datetime
    is_delayed: bool
    stale_age_seconds: int | None
    quality_flags: tuple[QualityFlag, ...]


@dataclass(frozen=True, slots=True)
class Quote:
    instrument_id: str
    bid_price: Decimal | None
    ask_price: Decimal | None
    last_price: Decimal | None
    as_of: datetime
    is_delayed: bool
    quality_flags: tuple[QualityFlag, ...]


@dataclass(frozen=True, slots=True)
class TradingCalendar:
    market: str
    version: str
    timezone: str
    trading_days: tuple[date, ...]


@dataclass(frozen=True, slots=True)
class DataSourceHealth:
    provider: str
    status: DataSourceStatus
    checked_at: datetime
    consecutive_failures: int
    last_success_at: datetime | None
    last_error_code: str | None
    stale_cache_available: bool
    stale_age_seconds: int | None


class IDataProvider(Protocol):
    async def search_instruments(self, query: str) -> Sequence[Instrument]: ...

    async def get_bars(self, request: BarsRequest) -> BarsResult: ...

    async def get_quote(self, instrument_id: str) -> Quote: ...

    async def get_calendar(self, market: str, start: date, end: date) -> TradingCalendar: ...


class IDataProviderHealth(Protocol):
    async def get_health(self, provider: str) -> DataSourceHealth: ...

