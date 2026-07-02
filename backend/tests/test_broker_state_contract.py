from __future__ import annotations

from app.application.broker_state_service import BrokerStateApplicationService
from app.domains.broker import BrokerStateResult, BrokerStateStatus
from app.infrastructure.broker_state_mapping import (
    BrokerGatewayExpectedError,
    ExpectedBrokerFailure,
    broker_expected_error_to_result,
)


def test_expected_broker_gateway_failures_are_typed_results() -> None:
    cases = {
        ExpectedBrokerFailure.CONNECTION_LOST: BrokerStateStatus.UNAVAILABLE,
        ExpectedBrokerFailure.TIMEOUT: BrokerStateStatus.STALE,
        ExpectedBrokerFailure.RATE_LIMITED: BrokerStateStatus.STALE,
        ExpectedBrokerFailure.SESSION_EXPIRED: BrokerStateStatus.UNAVAILABLE,
        ExpectedBrokerFailure.MAINTENANCE: BrokerStateStatus.UNAVAILABLE,
        ExpectedBrokerFailure.STATE_INCOMPLETE: BrokerStateStatus.RECONCILIATION_REQUIRED,
    }

    for failure, expected_status in cases.items():
        result = broker_expected_error_to_result(
            BrokerGatewayExpectedError(failure=failure, message=failure.value),
            trace_id="trace-broker",
        )

        assert result.status == expected_status
        assert result.state is None
        assert result.error_code == f"BROKER_{failure.value.upper()}"
        assert result.trace_id == "trace-broker"


async def _raise_unexpected() -> BrokerStateResult:
    raise RuntimeError("sdk payload corrupted")


class UnexpectedFailureGateway:
    async def get_state(self) -> BrokerStateResult:
        return await _raise_unexpected()


def test_unexpected_broker_failure_fails_closed() -> None:
    import asyncio

    service = BrokerStateApplicationService(UnexpectedFailureGateway())

    result = asyncio.run(service.get_state())

    assert result.status == BrokerStateStatus.UNAVAILABLE
    assert result.state is None
    assert result.error_code == "BROKER_STATE_UNKNOWN"

