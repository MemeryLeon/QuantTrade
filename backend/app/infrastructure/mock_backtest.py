from __future__ import annotations

from app.application.jobs import JobService, LEAN_BACKTEST_QUEUE
from app.domains.backtest import (
    BacktestMode,
    BacktestRequest,
    BacktestStatus,
    BacktestSubmission,
    IBacktestEngine,
)
from app.domains.jobs import JobState


class MockBacktestEngine(IBacktestEngine):
    def __init__(self, job_service: JobService) -> None:
        self._job_service = job_service

    async def submit(self, request: BacktestRequest) -> BacktestSubmission:
        if request.mode is not BacktestMode.MOCK:
            return BacktestSubmission(
                status=BacktestStatus.REJECTED,
                job_id=None,
                error_code="ENGINE_SCHEMA_INCOMPATIBLE",
                error_message="mock engine cannot run formal LEAN backtests",
                trace_id="mock-backtest",
            )

        handle = self._job_service.create_job(
            queue_name=LEAN_BACKTEST_QUEUE,
            task_name="mock_backtest",
            max_retries=1,
            timeout_seconds=300,
        )
        self._job_service.transition(
            handle.job_id,
            JobState.PREPARING_DATA,
            message="mock data prepared",
            progress_percent=25,
        )
        self._job_service.transition(
            handle.job_id,
            JobState.STARTING_ENGINE,
            message="mock engine starting",
            progress_percent=40,
        )
        self._job_service.transition(
            handle.job_id,
            JobState.RUNNING,
            message="mock engine running",
            progress_percent=60,
        )
        self._job_service.transition(
            handle.job_id,
            JobState.PARSING_RESULT,
            message="mock result parsed",
            progress_percent=90,
        )
        self._job_service.transition(
            handle.job_id,
            JobState.SUCCEEDED,
            message="mock backtest succeeded",
            progress_percent=100,
            artifact_uri="memory://mock-backtest/result",
        )
        return BacktestSubmission(
            status=BacktestStatus.ACCEPTED,
            job_id=handle.job_id,
            error_code=None,
            error_message=None,
            trace_id="mock-backtest",
        )
