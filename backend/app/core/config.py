from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    log_level: str
    trace_header_name: str


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("QUANTTRADE_APP_NAME", "QuantTrade API"),
        app_version=os.getenv("QUANTTRADE_APP_VERSION", "0.1.0"),
        environment=os.getenv("QUANTTRADE_ENV", "development"),
        log_level=os.getenv("QUANTTRADE_LOG_LEVEL", "INFO"),
        trace_header_name=os.getenv("QUANTTRADE_TRACE_HEADER", "X-Trace-ID"),
    )

