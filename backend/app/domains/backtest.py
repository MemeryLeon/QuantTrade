from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol, TypeAlias


ParameterValue: TypeAlias = str | int | float | bool | Decimal | date | datetime | None


class BacktestMode(StrEnum):
    MOCK = "mock"
    LEAN_FORMAL = "lean_formal"


class BacktestStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    strategy_version_id: str
    instruments: tuple[str, ...]
    start_date: date
    end_date: date
    resolution: str
    adjustment: str
    initial_capital: Decimal
    base_currency: str
    benchmark: str
    parameters: Mapping[str, ParameterValue]
    commission_model: str
    slippage_model: str
    data_snapshot_id: str
    mode: BacktestMode


@dataclass(frozen=True, slots=True)
class BacktestSubmission:
    status: BacktestStatus
    job_id: str | None
    error_code: str | None
    error_message: str | None
    trace_id: str


class IBacktestEngine(Protocol):
    async def submit(self, request: BacktestRequest) -> BacktestSubmission: ...

