from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


CHINA_A_MARKET = "CN_A"
CHINA_A_EXCHANGE_TIMEZONE = "Asia/Shanghai"


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


class MarketDataUse(StrEnum):
    DISPLAY = "display"
    FORMAL_SNAPSHOT = "formal_snapshot"
    FORMAL_BACKTEST = "formal_backtest"
    RISK = "risk"
    ORDER_DECISION = "order_decision"


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

    def __post_init__(self) -> None:
        _require_timezone_aware("start", self.start)
        _require_timezone_aware("end", self.end)
        if self.start > self.end:
            raise ValueError("bars request start must be before or equal to end")


@dataclass(frozen=True, slots=True)
class Bar:
    observed_at: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    quality_flags: tuple[QualityFlag, ...]

    def __post_init__(self) -> None:
        _require_timezone_aware("observed_at", self.observed_at)


@dataclass(frozen=True, slots=True)
class BarsResult:
    instrument_id: str
    bars: tuple[Bar, ...]
    as_of: datetime
    is_delayed: bool
    stale_age_seconds: int | None
    quality_flags: tuple[QualityFlag, ...]

    def __post_init__(self) -> None:
        _require_timezone_aware("as_of", self.as_of)
        if self.is_delayed:
            if self.stale_age_seconds is None:
                raise ValueError("delayed bars require stale_age_seconds")
            _require_quality_flag(self.quality_flags, QualityFlag.STALE_CACHE)
        if self.stale_age_seconds is not None and self.stale_age_seconds < 0:
            raise ValueError("stale_age_seconds must be non-negative")


@dataclass(frozen=True, slots=True)
class Quote:
    instrument_id: str
    bid_price: Decimal | None
    ask_price: Decimal | None
    last_price: Decimal | None
    as_of: datetime
    is_delayed: bool
    quality_flags: tuple[QualityFlag, ...]

    def __post_init__(self) -> None:
        _require_timezone_aware("as_of", self.as_of)
        if self.is_delayed:
            _require_quality_flag(self.quality_flags, QualityFlag.STALE_CACHE)


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

    def __post_init__(self) -> None:
        _require_timezone_aware("checked_at", self.checked_at)
        if self.last_success_at is not None:
            _require_timezone_aware("last_success_at", self.last_success_at)
        if self.consecutive_failures < 0:
            raise ValueError("consecutive_failures must be non-negative")
        if self.stale_age_seconds is not None and self.stale_age_seconds < 0:
            raise ValueError("stale_age_seconds must be non-negative")


class IDataProvider(Protocol):
    async def search_instruments(self, query: str) -> Sequence[Instrument]: ...

    async def get_bars(self, request: BarsRequest) -> BarsResult: ...

    async def get_quote(self, instrument_id: str) -> Quote: ...

    async def get_calendar(self, market: str, start: date, end: date) -> TradingCalendar: ...


class IDataProviderHealth(Protocol):
    async def get_health(self, provider: str) -> DataSourceHealth: ...


def ensure_market_data_allowed(result: BarsResult | Quote, use: MarketDataUse) -> None:
    if use is MarketDataUse.DISPLAY:
        return
    if result.is_delayed or QualityFlag.STALE_CACHE in result.quality_flags:
        raise ValueError("stale market data is only allowed for display")


def _require_timezone_aware(field_name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_quality_flag(flags: tuple[QualityFlag, ...], required: QualityFlag) -> None:
    if required not in flags:
        raise ValueError(f"delayed market data requires {required.value}")
