from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    trace_id: str
    details: Mapping[str, str]
