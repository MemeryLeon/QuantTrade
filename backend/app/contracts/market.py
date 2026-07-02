from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.market import DataSourceStatus, QualityFlag


MarketResolution = Literal["daily", "weekly", "monthly"]
AdjustmentMode = Literal["none", "qfq", "hfq"]


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


class QuoteResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    provider: Literal["akshare"]
    market: Literal["CN_A"]
    currency: Literal["CNY"]
    bid_price: Decimal | None
    ask_price: Decimal | None
    last_price: Decimal | None
    as_of: datetime
    is_delayed: bool
    quality_flags: tuple[QualityFlag, ...]


class BarsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    provider: Literal["akshare"]
    market: Literal["CN_A"]
    currency: Literal["CNY"]
    resolution: MarketResolution
    adjustment: AdjustmentMode
    timezone: Literal["Asia/Shanghai"]
    bars: tuple[BarResponse, ...]
    as_of: datetime
    is_delayed: bool
    stale_age_seconds: int | None
    quality_flags: tuple[QualityFlag, ...]


class IndicatorPointResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    observed_at: datetime
    sma: Decimal | None
    ema: Decimal | None
    macd: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    rsi: Decimal | None
    bollinger_middle: Decimal | None
    bollinger_upper: Decimal | None
    bollinger_lower: Decimal | None
    adx: Decimal | None


class IndicatorParametersResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    sma_period: int
    ema_period: int
    macd_fast_period: int
    macd_slow_period: int
    macd_signal_period: int
    rsi_period: int
    bollinger_period: int
    bollinger_multiplier: Decimal
    adx_period: int


class IndicatorsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    provider: Literal["akshare"]
    market: Literal["CN_A"]
    currency: Literal["CNY"]
    resolution: MarketResolution
    adjustment: AdjustmentMode
    timezone: Literal["Asia/Shanghai"]
    parameters: IndicatorParametersResponse
    points: tuple[IndicatorPointResponse, ...]
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
