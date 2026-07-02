from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.time import utc_now
from app.domains.jobs import JobHandle, JobLogEntry, JobState, JobStatus


DEFAULT_QUEUE = "default"
LEAN_BACKTEST_QUEUE = "lean_backtest"


ALLOWED_TRANSITIONS = {
    JobState.QUEUED: {
        JobState.PREPARING_DATA,
        JobState.RUNNING,
        JobState.CANCELLED,
        JobState.FAILED,
        JobState.TIMED_OUT,
    },
    JobState.PREPARING_DATA: {JobState.STARTING_ENGINE, JobState.CANCELLED, JobState.FAILED},
    JobState.STARTING_ENGINE: {JobState.RUNNING, JobState.CANCELLED, JobState.FAILED},
    JobState.RUNNING: {
        JobState.PARSING_RESULT,
        JobState.SUCCEEDED,
        JobState.CANCELLED,
        JobState.FAILED,
        JobState.TIMED_OUT,
    },
    JobState.PARSING_RESULT: {JobState.SUCCEEDED, JobState.CANCELLED, JobState.FAILED},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: set(),
    JobState.CANCELLED: set(),
    JobState.TIMED_OUT: set(),
}


@dataclass(frozen=True, slots=True)
class JobRecord:
    job_id: str
    queue_name: str
    task_name: str
    state: JobState
    progress_percent: int
    message: str | None
    error_code: str | None
    artifact_uri: str | None
    retry_count: int
    max_retries: int
    timeout_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JobTransitionError(ValueError):
    pass


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._logs: dict[str, list[JobLogEntry]] = {}

    def save(self, record: JobRecord) -> None:
        self._jobs[record.job_id] = record

    def get(self, job_id: str) -> JobRecord:
        return self._jobs[job_id]

    def add_log(self, entry: JobLogEntry) -> None:
        self._logs.setdefault(entry.job_id, []).append(entry)

    def logs(self, job_id: str) -> tuple[JobLogEntry, ...]:
        return tuple(self._logs.get(job_id, ()))


class JobService:
    def __init__(self, repository: InMemoryJobRepository) -> None:
        self._repository = repository

    def create_job(
        self,
        queue_name: str,
        task_name: str,
        max_retries: int,
        timeout_seconds: int | None,
    ) -> JobHandle:
        now = utc_now()
        job_id = str(uuid4())
        timeout_at = now + timedelta(seconds=timeout_seconds) if timeout_seconds is not None else None
        record = JobRecord(
            job_id=job_id,
            queue_name=queue_name,
            task_name=task_name,
            state=JobState.QUEUED,
            progress_percent=0,
            message="queued",
            error_code=None,
            artifact_uri=None,
            retry_count=0,
            max_retries=max_retries,
            timeout_at=timeout_at,
            created_at=now,
            updated_at=now,
        )
        self._repository.save(record)
        self.append_log(job_id, "job queued")
        return JobHandle(job_id=job_id, queue_name=queue_name, state=JobState.QUEUED, created_at=now)

    def transition(
        self,
        job_id: str,
        next_state: JobState,
        message: str | None = None,
        progress_percent: int | None = None,
        error_code: str | None = None,
        artifact_uri: str | None = None,
    ) -> JobStatus:
        record = self._repository.get(job_id)
        if next_state not in ALLOWED_TRANSITIONS[record.state]:
            raise JobTransitionError(f"invalid job transition {record.state} -> {next_state}")
        progress = record.progress_percent if progress_percent is None else progress_percent
        if progress < 0 or progress > 100:
            raise ValueError("job progress must be between 0 and 100")
        updated = replace(
            record,
            state=next_state,
            progress_percent=progress,
            message=message,
            error_code=error_code,
            artifact_uri=artifact_uri or record.artifact_uri,
            updated_at=utc_now(),
        )
        self._repository.save(updated)
        self.append_log(job_id, message or next_state.value)
        return self.status(job_id)

    def append_log(self, job_id: str, message: str) -> None:
        self._repository.add_log(JobLogEntry(job_id=job_id, message=message, created_at=utc_now()))

    def cancel(self, job_id: str) -> JobStatus:
        return self.transition(job_id, JobState.CANCELLED, message="cancelled by operator")

    def mark_timed_out(self, job_id: str) -> JobStatus:
        return self.transition(
            job_id,
            JobState.TIMED_OUT,
            message="job timed out",
            error_code="ENGINE_TIMEOUT",
        )

    def retry_or_fail(self, job_id: str, error_code: str, message: str) -> JobStatus:
        record = self._repository.get(job_id)
        if record.retry_count < record.max_retries:
            updated = replace(
                record,
                state=JobState.QUEUED,
                retry_count=record.retry_count + 1,
                message="retry queued",
                updated_at=utc_now(),
            )
            self._repository.save(updated)
            self.append_log(job_id, "retry queued")
            return self.status(job_id)
        return self.transition(job_id, JobState.FAILED, message=message, error_code=error_code)

    def status(self, job_id: str) -> JobStatus:
        record = self._repository.get(job_id)
        return JobStatus(
            job_id=record.job_id,
            state=record.state,
            progress_percent=record.progress_percent,
            message=record.message,
            updated_at=record.updated_at,
            retry_count=record.retry_count,
            max_retries=record.max_retries,
            artifact_uri=record.artifact_uri,
        )

    def logs(self, job_id: str) -> tuple[JobLogEntry, ...]:
        return self._repository.logs(job_id)
