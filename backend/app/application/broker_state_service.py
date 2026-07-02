from __future__ import annotations

import logging

from app.core.trace import get_trace_id
from app.domains.broker import BrokerStateResult, BrokerStateStatus, IBrokerGateway


logger = logging.getLogger(__name__)


class BrokerStateApplicationService:
    def __init__(self, gateway: IBrokerGateway) -> None:
        self._gateway = gateway

    async def get_state(self) -> BrokerStateResult:
        try:
            return await self._gateway.get_state()
        except Exception:
            trace_id = get_trace_id()
            logger.exception("Unexpected broker state boundary failure")
            return BrokerStateResult(
                status=BrokerStateStatus.UNAVAILABLE,
                state=None,
                as_of=None,
                error_code="BROKER_STATE_UNKNOWN",
                error_message="broker state unavailable; request failed closed",
                trace_id=trace_id,
            )

