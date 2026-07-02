from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4


_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def new_trace_id() -> str:
    return uuid4().hex


def get_trace_id() -> str:
    current = _trace_id.get()
    if current is not None:
        return current
    generated = new_trace_id()
    set_trace_id(generated)
    return generated


def set_trace_id(trace_id: str) -> None:
    _trace_id.set(trace_id)

