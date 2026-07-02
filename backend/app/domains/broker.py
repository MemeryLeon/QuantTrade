from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol


class BrokerStateStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class BrokerConnectionStatus(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class BrokerState:
    broker_account_id: str
    broker_state_as_of: datetime
    broker_state_status: BrokerStateStatus
    max_state_staleness_seconds: int
    connection_status: BrokerConnectionStatus
    cash_available: Decimal | None
    gross_exposure: Decimal | None
    open_order_count: int | None
    reconciliation_completed: bool


@dataclass(frozen=True, slots=True)
class BrokerStateResult:
    status: BrokerStateStatus
    state: BrokerState | None
    as_of: datetime | None
    error_code: str | None
    error_message: str | None
    trace_id: str


class IBrokerGateway(Protocol):
    async def get_state(self) -> BrokerStateResult: ...

