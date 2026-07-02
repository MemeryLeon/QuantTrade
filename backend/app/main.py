from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.contracts.system import ApiErrorResponse
from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.logging import configure_logging
from app.core.middleware import trace_id_middleware
from app.core.trace import get_trace_id


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.middleware("http")(trace_id_middleware)
app.include_router(api_router)


@app.exception_handler(ApiError)
async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
    body = ApiErrorResponse(
        code=exc.code,
        message=exc.message,
        trace_id=get_trace_id(),
        details=exc.details,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())
