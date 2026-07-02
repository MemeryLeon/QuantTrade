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
    database_url: str
    redis_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool
    minio_bucket_lean_artifacts: str
    market_provider: str
    market_failure_threshold: int
    market_recovery_cooldown_seconds: int
    market_cache_ttl_seconds: int
    market_cache_freshness_seconds: int
    market_max_stale_cache_age_seconds: int
    market_cache_max_value_bytes: int
    celery_broker_url: str
    celery_result_backend: str
    lean_worker_concurrency: int
    worker_prefetch_multiplier: int


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("QUANTTRADE_APP_NAME", "QuantTrade API"),
        app_version=os.getenv("QUANTTRADE_APP_VERSION", "0.1.0"),
        environment=os.getenv("QUANTTRADE_ENV", "development"),
        log_level=os.getenv("QUANTTRADE_LOG_LEVEL", "INFO"),
        trace_header_name=os.getenv("QUANTTRADE_TRACE_HEADER", "X-Trace-ID"),
        database_url=_database_url(),
        redis_url=_redis_url(),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        minio_access_key=os.getenv("MINIO_ROOT_USER", "quanttrade_minio"),
        minio_secret_key=os.getenv("MINIO_ROOT_PASSWORD", "quanttrade_minio_dev_password"),
        minio_secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        minio_bucket_lean_artifacts=os.getenv(
            "MINIO_BUCKET_LEAN_ARTIFACTS",
            "quanttrade-lean-artifacts",
        ),
        market_provider=os.getenv("MARKET_PROVIDER", "akshare"),
        market_failure_threshold=int(os.getenv("MARKET_FAILURE_THRESHOLD", "3")),
        market_recovery_cooldown_seconds=int(
            os.getenv("MARKET_RECOVERY_COOLDOWN_SECONDS", "300")
        ),
        market_cache_ttl_seconds=int(os.getenv("MARKET_CACHE_TTL_SECONDS", "86400")),
        market_cache_freshness_seconds=int(os.getenv("MARKET_CACHE_FRESHNESS_SECONDS", "300")),
        market_max_stale_cache_age_seconds=int(
            os.getenv("MARKET_MAX_STALE_CACHE_AGE_SECONDS", "86400")
        ),
        market_cache_max_value_bytes=int(os.getenv("MARKET_CACHE_MAX_VALUE_BYTES", "2097152")),
        celery_broker_url=os.getenv("CELERY_BROKER_URL", _redis_url()),
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND", _redis_url()),
        lean_worker_concurrency=int(os.getenv("LEAN_WORKER_CONCURRENCY", "1")),
        worker_prefetch_multiplier=int(os.getenv("WORKER_PREFETCH_MULTIPLIER", "1")),
    )


def _database_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "quanttrade")
    user = os.getenv("POSTGRES_USER", "quanttrade")
    password = os.getenv("POSTGRES_PASSWORD", "quanttrade_dev_password")
    return os.getenv("DATABASE_URL", f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}")


def _redis_url() -> str:
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    return os.getenv("REDIS_URL", f"redis://{host}:{port}/{db}")
