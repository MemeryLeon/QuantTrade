from __future__ import annotations

from dataclasses import dataclass

from celery import Celery
from kombu import Queue

from app.application.jobs import DEFAULT_QUEUE, LEAN_BACKTEST_QUEUE
from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class WorkerQueueSettings:
    default_queue: str
    lean_backtest_queue: str
    worker_prefetch_multiplier: int
    lean_worker_concurrency: int


def get_worker_queue_settings() -> WorkerQueueSettings:
    settings = get_settings()
    return WorkerQueueSettings(
        default_queue=DEFAULT_QUEUE,
        lean_backtest_queue=LEAN_BACKTEST_QUEUE,
        worker_prefetch_multiplier=settings.worker_prefetch_multiplier,
        lean_worker_concurrency=settings.lean_worker_concurrency,
    )


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "quanttrade",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    app.conf.task_default_queue = DEFAULT_QUEUE
    app.conf.task_queues = (
        Queue(DEFAULT_QUEUE),
        Queue(LEAN_BACKTEST_QUEUE),
    )
    app.conf.task_routes = {
        "app.workers.tasks.run_lean_backtest": {"queue": LEAN_BACKTEST_QUEUE},
    }
    app.conf.worker_prefetch_multiplier = settings.worker_prefetch_multiplier
    app.conf.task_acks_late = True
    return app


celery_app = create_celery_app()
