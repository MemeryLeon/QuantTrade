from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.backtest import BacktestStatus
from app.domains.jobs import JobState


ParameterInputValue = str | int | float | bool | None


class BacktestParameterInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    value: ParameterInputValue


class MockBacktestRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy_version_id: str = Field(min_length=1)
    instruments: tuple[str, ...] = Field(min_length=1)
    start_date: date
    end_date: date
    resolution: Literal["daily"]
    adjustment: Literal["qfq", "hfq", "none"]
    initial_capital: Decimal = Field(gt=0)
    base_currency: Literal["CNY"]
    benchmark: str = Field(min_length=1)
    parameters: tuple[BacktestParameterInput, ...] = ()
    commission_model: Literal["mock"]
    slippage_model: Literal["mock"]
    data_snapshot_id: str = Field(min_length=1)


class BacktestSubmissionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: BacktestStatus
    job_id: str | None
    error_code: str | None
    error_message: str | None
    trace_id: str


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    state: JobState
    progress_percent: int
    message: str | None
    updated_at: datetime
    retry_count: int
    max_retries: int
    artifact_uri: str | None


class JobLogEntryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    message: str
    created_at: datetime


class JobLogsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    entries: tuple[JobLogEntryResponse, ...]


class MockBacktestResultResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    state: JobState
    artifact_uri: str
    total_return_percent: float
    max_drawdown_percent: float
    trade_count: int
