from __future__ import annotations

from app.application.jobs import DEFAULT_QUEUE, LEAN_BACKTEST_QUEUE
from app.workers.celery_app import create_celery_app, get_worker_queue_settings


def test_celery_queues_and_lean_resource_limits_are_fixed() -> None:
    settings = get_worker_queue_settings()
    app = create_celery_app()

    assert settings.default_queue == DEFAULT_QUEUE
    assert settings.lean_backtest_queue == LEAN_BACKTEST_QUEUE
    assert settings.lean_worker_concurrency == 1
    assert settings.worker_prefetch_multiplier == 1
    assert app.conf.task_default_queue == DEFAULT_QUEUE
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.task_routes["app.workers.tasks.run_lean_backtest"]["queue"] == LEAN_BACKTEST_QUEUE
