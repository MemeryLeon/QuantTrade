from __future__ import annotations

from fastapi import APIRouter

from app.contracts.system import HealthResponse


router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")

