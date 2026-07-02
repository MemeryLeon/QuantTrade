from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_backtest_service
from app.application.backtests import BacktestApplicationService
from app.contracts.backtests import (
    BacktestSubmissionResponse,
    JobLogEntryResponse,
    JobLogsResponse,
    JobStatusResponse,
    MockBacktestRequest,
    MockBacktestResultResponse,
)
from app.core.errors import ApiError
from app.core.trace import get_trace_id
from app.domains.backtest import BacktestMode, BacktestRequest


router = APIRouter(tags=["backtests"])


def _not_found(job_id: str) -> ApiError:
    return ApiError(
        status_code=404,
        code="DATA_NOT_FOUND",
        message="job not found",
        details={"job_id": job_id},
    )


@router.post("/backtests/mock")
async def submit_mock_backtest(
    request: MockBacktestRequest,
    service: BacktestApplicationService = Depends(get_backtest_service),
) -> BacktestSubmissionResponse:
    submission = await service.submit(
        BacktestRequest(
            strategy_version_id=request.strategy_version_id,
            instruments=request.instruments,
            start_date=request.start_date,
            end_date=request.end_date,
            resolution=request.resolution,
            adjustment=request.adjustment,
            initial_capital=Decimal(request.initial_capital),
            base_currency=request.base_currency,
            benchmark=request.benchmark,
            parameters={parameter.name: parameter.value for parameter in request.parameters},
            commission_model=request.commission_model,
            slippage_model=request.slippage_model,
            data_snapshot_id=request.data_snapshot_id,
            mode=BacktestMode.MOCK,
        )
    )
    return BacktestSubmissionResponse(
        status=submission.status,
        job_id=submission.job_id,
        error_code=submission.error_code,
        error_message=submission.error_message,
        trace_id=get_trace_id(),
    )


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    service: BacktestApplicationService = Depends(get_backtest_service),
) -> JobStatusResponse:
    try:
        status = service.status(job_id)
    except KeyError as exc:
        raise _not_found(job_id) from exc
    return JobStatusResponse(
        job_id=status.job_id,
        state=status.state,
        progress_percent=status.progress_percent,
        message=status.message,
        updated_at=status.updated_at,
        retry_count=status.retry_count,
        max_retries=status.max_retries,
        artifact_uri=status.artifact_uri,
    )


@router.get("/jobs/{job_id}/logs")
def get_job_logs(
    job_id: str,
    service: BacktestApplicationService = Depends(get_backtest_service),
) -> JobLogsResponse:
    try:
        service.status(job_id)
        logs = service.logs(job_id)
    except KeyError as exc:
        raise _not_found(job_id) from exc
    return JobLogsResponse(
        entries=tuple(
            JobLogEntryResponse(
                job_id=entry.job_id,
                message=entry.message,
                created_at=entry.created_at,
            )
            for entry in logs
        )
    )


@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    service: BacktestApplicationService = Depends(get_backtest_service),
) -> JobStatusResponse:
    try:
        status = service.cancel(job_id)
    except KeyError as exc:
        raise _not_found(job_id) from exc
    except ValueError as exc:
        raise ApiError(
            status_code=409,
            code="VALIDATION_ERROR",
            message="job cannot be cancelled from its current state",
            details={"job_id": job_id},
        ) from exc
    return JobStatusResponse(
        job_id=status.job_id,
        state=status.state,
        progress_percent=status.progress_percent,
        message=status.message,
        updated_at=status.updated_at,
        retry_count=status.retry_count,
        max_retries=status.max_retries,
        artifact_uri=status.artifact_uri,
    )


@router.get("/backtests/mock/{job_id}/result")
def get_mock_backtest_result(
    job_id: str,
    service: BacktestApplicationService = Depends(get_backtest_service),
) -> MockBacktestResultResponse:
    try:
        result = service.mock_result(job_id)
    except KeyError as exc:
        raise _not_found(job_id) from exc
    except ValueError as exc:
        raise ApiError(
            status_code=409,
            code="BACKTEST_FAILED",
            message="mock backtest result is not available",
            details={"job_id": job_id},
        ) from exc
    return MockBacktestResultResponse(
        job_id=result.job_id,
        state=result.state,
        artifact_uri=result.artifact_uri,
        total_return_percent=result.total_return_percent,
        max_drawdown_percent=result.max_drawdown_percent,
        trade_count=result.trade_count,
    )
