from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.backtests import router as backtests_router
from app.api.v1.system import router as system_router


api_router = APIRouter()
api_router.include_router(backtests_router)
api_router.include_router(system_router)
