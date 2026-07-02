from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.core.time import utc_now
from app.domains.jobs import IJobQueue, JobHandle, JobState, JobStatus


class InMemoryJobQueue(IJobQueue):
    def __init__(self) -> None:
        self._jobs: dict[str, JobStatus] = {}

    async def enqueue(self, queue_name: str, task_name: str, payload: bytes) -> JobHandle:
        if not payload:
            raise ValueError("job payload must not be empty")
        now = utc_now()
        job_id = str(uuid4())
        self._jobs[job_id] = JobStatus(
            job_id=job_id,
            state=JobState.QUEUED,
            progress_percent=0,
            message=task_name,
            updated_at=now,
            retry_count=0,
            max_retries=0,
            artifact_uri=None,
        )
        return JobHandle(job_id=job_id, queue_name=queue_name, state=JobState.QUEUED, created_at=now)

    async def get_status(self, job_id: str) -> JobStatus:
        return self._jobs[job_id]

    async def cancel(self, job_id: str) -> JobStatus:
        current = self._jobs[job_id]
        cancelled = JobStatus(
            job_id=current.job_id,
            state=JobState.CANCELLED,
            progress_percent=current.progress_percent,
            message="cancelled",
            updated_at=datetime.now(current.updated_at.tzinfo),
            retry_count=current.retry_count,
            max_retries=current.max_retries,
            artifact_uri=current.artifact_uri,
        )
        self._jobs[job_id] = cancelled
        return cancelled

