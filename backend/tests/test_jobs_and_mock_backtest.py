from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

from app.application.jobs import InMemoryJobRepository, JobService, LEAN_BACKTEST_QUEUE
from app.domains.backtest import BacktestMode, BacktestRequest, BacktestStatus
from app.domains.jobs import JobState
from app.infrastructure.mock_backtest import MockBacktestEngine


def test_job_state_machine_supports_cancel_timeout_and_retry() -> None:
    repository = InMemoryJobRepository()
    service = JobService(repository)
    handle = service.create_job(
        queue_name=LEAN_BACKTEST_QUEUE,
        task_name="mock_backtest",
        max_retries=1,
        timeout_seconds=30,
    )

    service.transition(handle.job_id, JobState.RUNNING, progress_percent=50, message="running")
    retry_status = service.retry_or_fail(handle.job_id, "BACKTEST_FAILED", "failed once")

    assert retry_status.state == JobState.QUEUED
    assert retry_status.retry_count == 1

    service.transition(handle.job_id, JobState.RUNNING, progress_percent=50, message="running again")
    timeout_status = service.mark_timed_out(handle.job_id)

    assert timeout_status.state == JobState.TIMED_OUT
    assert timeout_status.message == "job timed out"
    assert len(service.logs(handle.job_id)) >= 4


def test_job_state_machine_rejects_invalid_transition() -> None:
    repository = InMemoryJobRepository()
    service = JobService(repository)
    handle = service.create_job("default", "task", max_retries=0, timeout_seconds=None)

    try:
        service.transition(handle.job_id, JobState.SUCCEEDED)
    except ValueError as exc:
        assert "invalid job transition" in str(exc)
    else:
        raise AssertionError("expected invalid transition error")


def test_mock_backtest_engine_completes_backend_loop() -> None:
    repository = InMemoryJobRepository()
    service = JobService(repository)
    engine = MockBacktestEngine(service)
    request = BacktestRequest(
        strategy_version_id="strategy-version-1",
        instruments=("000001.SZ",),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        resolution="daily",
        adjustment="qfq",
        initial_capital=Decimal("100000.00"),
        base_currency="CNY",
        benchmark="000300.SH",
        parameters={"fast": 5, "slow": 20},
        commission_model="mock",
        slippage_model="mock",
        data_snapshot_id="snapshot-1",
        mode=BacktestMode.MOCK,
    )

    submission = asyncio.run(engine.submit(request))

    assert submission.status == BacktestStatus.ACCEPTED
    assert submission.job_id is not None
    status = service.status(submission.job_id)
    assert status.state == JobState.SUCCEEDED
    assert status.progress_percent == 100
    assert status.artifact_uri == "memory://mock-backtest/result"


def test_mock_backtest_engine_rejects_formal_mode() -> None:
    repository = InMemoryJobRepository()
    service = JobService(repository)
    engine = MockBacktestEngine(service)
    request = BacktestRequest(
        strategy_version_id="strategy-version-1",
        instruments=("000001.SZ",),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        resolution="daily",
        adjustment="qfq",
        initial_capital=Decimal("100000.00"),
        base_currency="CNY",
        benchmark="000300.SH",
        parameters={},
        commission_model="mock",
        slippage_model="mock",
        data_snapshot_id="snapshot-1",
        mode=BacktestMode.LEAN_FORMAL,
    )

    submission = asyncio.run(engine.submit(request))

    assert submission.status == BacktestStatus.REJECTED
    assert submission.error_code == "ENGINE_SCHEMA_INCOMPATIBLE"

