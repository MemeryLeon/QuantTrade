from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class JobState(StrEnum):
    QUEUED = "queued"
    PREPARING_DATA = "preparing_data"
    STARTING_ENGINE = "starting_engine"
    RUNNING = "running"
    PARSING_RESULT = "parsing_result"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class JobHandle:
    job_id: str
    queue_name: str
    state: JobState
    created_at: datetime


@dataclass(frozen=True, slots=True)
class JobStatus:
    job_id: str
    state: JobState
    progress_percent: int
    message: str | None
    updated_at: datetime
    retry_count: int
    max_retries: int
    artifact_uri: str | None


@dataclass(frozen=True, slots=True)
class JobLogEntry:
    job_id: str
    message: str
    created_at: datetime


class IJobQueue(Protocol):
    async def enqueue(self, queue_name: str, task_name: str, payload: bytes) -> JobHandle: ...

    async def get_status(self, job_id: str) -> JobStatus: ...

    async def cancel(self, job_id: str) -> JobStatus: ...
