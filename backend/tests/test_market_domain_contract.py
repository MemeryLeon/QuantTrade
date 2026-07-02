from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.domains.market import (
    Bar,
    BarsRequest,
    BarsResult,
    DataSourceHealth,
    DataSourceStatus,
    MarketDataUse,
    QualityFlag,
    ensure_market_data_allowed,
)


def test_market_datetimes_must_be_timezone_aware() -> None:
    naive = datetime(2026, 7, 2, 9, 30)

    with pytest.raises(ValueError, match="timezone-aware"):
        BarsRequest(
            instrument_id="CN_A:000001",
            start=naive,
            end=naive,
            resolution="daily",
            adjustment="none",
        )


def test_delayed_bars_require_stale_cache_flag_and_age() -> None:
    now = datetime(2026, 7, 2, 15, 0, tzinfo=timezone.utc)
    bar = Bar(
        observed_at=now,
        open_price=Decimal("10.00"),
        high_price=Decimal("10.20"),
        low_price=Decimal("9.90"),
        close_price=Decimal("10.10"),
        volume=1000,
        quality_flags=(),
    )

    with pytest.raises(ValueError, match="STALE_CACHE"):
        BarsResult(
            instrument_id="CN_A:000001",
            bars=(bar,),
            as_of=now,
            is_delayed=True,
            stale_age_seconds=60,
            quality_flags=(),
        )


def test_stale_cache_is_only_allowed_for_display() -> None:
    now = datetime(2026, 7, 2, 15, 0, tzinfo=timezone.utc)
    delayed = BarsResult(
        instrument_id="CN_A:000001",
        bars=(),
        as_of=now,
        is_delayed=True,
        stale_age_seconds=60,
        quality_flags=(QualityFlag.STALE_CACHE, QualityFlag.PROVIDER_DEGRADED),
    )

    ensure_market_data_allowed(delayed, MarketDataUse.DISPLAY)
    with pytest.raises(ValueError, match="only allowed for display"):
        ensure_market_data_allowed(delayed, MarketDataUse.FORMAL_SNAPSHOT)
    with pytest.raises(ValueError, match="only allowed for display"):
        ensure_market_data_allowed(delayed, MarketDataUse.FORMAL_BACKTEST)
    with pytest.raises(ValueError, match="only allowed for display"):
        ensure_market_data_allowed(delayed, MarketDataUse.RISK)
    with pytest.raises(ValueError, match="only allowed for display"):
        ensure_market_data_allowed(delayed, MarketDataUse.ORDER_DECISION)


def test_data_source_health_contract_validates_status_fields() -> None:
    checked_at = datetime(2026, 7, 2, 15, 0, tzinfo=timezone.utc)

    health = DataSourceHealth(
        provider="akshare",
        status=DataSourceStatus.DEGRADED,
        checked_at=checked_at,
        consecutive_failures=3,
        last_success_at=checked_at,
        last_error_code="TIMEOUT",
        stale_cache_available=True,
        stale_age_seconds=3600,
    )

    assert health.status is DataSourceStatus.DEGRADED
    assert health.stale_cache_available is True

