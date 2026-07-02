from __future__ import annotations

from dataclasses import dataclass

from app.domains.backtest import BacktestRequest, BacktestSubmission, IBacktestEngine
from app.domains.jobs import JobLogEntry, JobState, JobStatus
from app.application.jobs import JobService


@dataclass(frozen=True, slots=True)
class MockBacktestResult:
    job_id: str
    state: JobState
    artifact_uri: str
    total_return_percent: float
    max_drawdown_percent: float
    trade_count: int


class BacktestApplicationService:
    def __init__(self, engine: IBacktestEngine, job_service: JobService) -> None:
        self._engine = engine
        self._job_service = job_service

    async def submit(self, request: BacktestRequest) -> BacktestSubmission:
        return await self._engine.submit(request)

    def status(self, job_id: str) -> JobStatus:
        return self._job_service.status(job_id)

    def logs(self, job_id: str) -> tuple[JobLogEntry, ...]:
        return self._job_service.logs(job_id)

    def cancel(self, job_id: str) -> JobStatus:
        return self._job_service.cancel(job_id)

    def mock_result(self, job_id: str) -> MockBacktestResult:
        status = self.status(job_id)
        if status.state is not JobState.SUCCEEDED or status.artifact_uri is None:
            raise ValueError("mock backtest result is not available")
        return MockBacktestResult(
            job_id=job_id,
            state=status.state,
            artifact_uri=status.artifact_uri,
            total_return_percent=3.42,
            max_drawdown_percent=1.15,
            trade_count=4,
        )
