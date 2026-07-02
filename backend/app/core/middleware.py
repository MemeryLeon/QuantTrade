from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.trace import new_trace_id, set_trace_id


async def trace_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    header_name = "X-Trace-ID"
    trace_id = request.headers.get(header_name) or new_trace_id()
    set_trace_id(trace_id)
    response = await call_next(request)
    response.headers[header_name] = trace_id
    return response

