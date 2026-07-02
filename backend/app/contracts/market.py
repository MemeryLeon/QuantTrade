from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.market import DataSourceStatus, QualityFlag


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    symbol: str
    name: str
    market: str
    exchange_timezone: str


class InstrumentSearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    instruments: tuple[InstrumentResponse, ...]


class BarResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    observed_at: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    quality_flags: tuple[QualityFlag, ...]


class BarsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    provider: Literal["akshare"]
    market: Literal["CN_A"]
    currency: Literal["CNY"]
    resolution: Literal["daily"]
    adjustment: Literal["none", "qfq", "hfq"]
    timezone: Literal["Asia/Shanghai"]
    bars: tuple[BarResponse, ...]
    as_of: datetime
    is_delayed: bool
    stale_age_seconds: int | None
    quality_flags: tuple[QualityFlag, ...]


class TradingCalendarResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    market: str
    version: str
    timezone: str
    trading_days: tuple[date, ...]


class DataSourceHealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str
    status: DataSourceStatus
    checked_at: datetime
    consecutive_failures: int = Field(ge=0)
    last_success_at: datetime | None
    last_error_code: str | None
    stale_cache_available: bool
    stale_age_seconds: int | None

