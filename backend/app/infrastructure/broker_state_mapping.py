from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domains.broker import BrokerStateResult, BrokerStateStatus


class ExpectedBrokerFailure(StrEnum):
    CONNECTION_LOST = "connection_lost"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    SESSION_EXPIRED = "session_expired"
    MAINTENANCE = "maintenance"
    STATE_INCOMPLETE = "state_incomplete"


@dataclass(frozen=True, slots=True)
class BrokerGatewayExpectedError(Exception):
    failure: ExpectedBrokerFailure
    message: str


_EXPECTED_STATUS = {
    ExpectedBrokerFailure.CONNECTION_LOST: BrokerStateStatus.UNAVAILABLE,
    ExpectedBrokerFailure.TIMEOUT: BrokerStateStatus.STALE,
    ExpectedBrokerFailure.RATE_LIMITED: BrokerStateStatus.STALE,
    ExpectedBrokerFailure.SESSION_EXPIRED: BrokerStateStatus.UNAVAILABLE,
    ExpectedBrokerFailure.MAINTENANCE: BrokerStateStatus.UNAVAILABLE,
    ExpectedBrokerFailure.STATE_INCOMPLETE: BrokerStateStatus.RECONCILIATION_REQUIRED,
}


def broker_expected_error_to_result(
    error: BrokerGatewayExpectedError,
    trace_id: str,
    as_of: datetime | None = None,
) -> BrokerStateResult:
    return BrokerStateResult(
        status=_EXPECTED_STATUS[error.failure],
        state=None,
        as_of=as_of,
        error_code=f"BROKER_{error.failure.value.upper()}",
        error_message=error.message,
        trace_id=trace_id,
    )

