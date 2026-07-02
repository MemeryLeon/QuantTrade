from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_market_data_service
from app.application.market_data import MarketDataApplicationService
from app.core.config import get_settings
from app.domains.market import BarsRequest, DataSourceStatus, QualityFlag
from app.infrastructure.akshare_market_data import AKSHARE_PROVIDER, AkshareDataProvider
from app.infrastructure.cache import RedisCache
from app.main import app


class FakeFrame:
    def __init__(self, records: list[dict[str, object]]) -> None:
        self._records = records

    def to_dict(self, orient: str) -> list[dict[str, object]]:
        assert orient == "records"
        return self._records


class FakeAkshare:
    def __init__(self) -> None:
        self.fail_hist = False
        self.hist_calls = 0

    def stock_zh_a_spot_em(self) -> FakeFrame:
        return FakeFrame(
            [
                {"代码": "000001", "名称": "平安银行", "最新价": "10.10"},
                {"代码": "600000", "名称": "浦发银行", "最新价": "8.20"},
            ]
        )

    def stock_zh_a_hist(
        self,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
        timeout: float | None = None,
    ) -> FakeFrame:
        self.hist_calls += 1
        assert symbol == "000001"
        assert period == "daily"
        assert adjust == ""
        if self.fail_hist:
            raise RuntimeError("provider timeout")
        start = datetime.strptime(start_date, "%Y%m%d").date()
        end = datetime.strptime(end_date, "%Y%m%d").date()
        records = []
        for day in range(1, 31):
            observed = datetime(2026, 7, day).date()
            if not start <= observed <= end:
                continue
            close = Decimal("10.00") + (Decimal(day) / Decimal("10"))
            records.append(
                {
                    "日期": f"2026-07-{day:02d}",
                    "开盘": str(close - Decimal("0.10")),
                    "收盘": str(close),
                    "最高": str(close + Decimal("0.20")),
                    "最低": str(close - Decimal("0.30")),
                    "成交量": str(999 + day),
                }
            )
        return FakeFrame(records)

    def tool_trade_date_hist_sina(self) -> FakeFrame:
        return FakeFrame(
            [
                {"trade_date": "2026-07-01"},
                {"trade_date": "2026-07-02"},
                {"trade_date": "2026-07-05"},
            ]
        )


class FakeRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[bytes, bytes]] = {}
        self.expirations: dict[str, int] = {}

    def hset(self, key: str, mapping: dict[str, bytes]) -> None:
        self.hashes[key] = {name.encode("utf-8"): value for name, value in mapping.items()}

    def expire(self, key: str, ttl_seconds: int) -> None:
        self.expirations[key] = ttl_seconds

    def hgetall(self, key: str) -> dict[bytes, bytes]:
        return self.hashes.get(key, {})


def _provider(
    fake_akshare: FakeAkshare,
    fake_redis: FakeRedis,
    *,
    max_value_bytes: int = 4096,
) -> AkshareDataProvider:
    settings = replace(
        get_settings(),
        market_failure_threshold=2,
        market_recovery_cooldown_seconds=300,
        market_cache_ttl_seconds=86_400,
        market_cache_freshness_seconds=-1,
        market_max_stale_cache_age_seconds=86_400,
        market_cache_max_value_bytes=max_value_bytes,
    )
    return AkshareDataProvider(
        akshare_factory=lambda: fake_akshare,
        cache=RedisCache(fake_redis),  # type: ignore[arg-type]
        settings=settings,
    )


def _request() -> BarsRequest:
    return BarsRequest(
        instrument_id="CN_A:000001",
        start=datetime(2026, 7, 1, tzinfo=timezone.utc),
        end=datetime(2026, 7, 2, tzinfo=timezone.utc),
        resolution="daily",
        adjustment="none",
    )


def test_akshare_provider_searches_a_share_instruments() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis())

    instruments = asyncio.run(provider.search_instruments("平安"))

    assert len(instruments) == 1
    assert instruments[0].instrument_id == "CN_A:000001"
    assert instruments[0].exchange_timezone == "Asia/Shanghai"


def test_akshare_provider_returns_daily_bars_and_calendar() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis())

    bars = asyncio.run(provider.get_bars(_request()))
    calendar = asyncio.run(
        provider.get_calendar(
            "CN_A",
            datetime(2026, 7, 1, tzinfo=timezone.utc).date(),
            datetime(2026, 7, 2, tzinfo=timezone.utc).date(),
        )
    )

    assert bars.bars[0].close_price == Decimal("10.10")
    assert bars.bars[0].volume == 1000
    assert bars.as_of == bars.bars[-1].observed_at
    assert calendar.trading_days == (
        datetime(2026, 7, 1, tzinfo=timezone.utc).date(),
        datetime(2026, 7, 2, tzinfo=timezone.utc).date(),
    )


def test_akshare_provider_aggregates_weekly_and_monthly_bars_from_daily_bars() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis())
    base_request = BarsRequest(
        instrument_id="CN_A:000001",
        start=datetime(2026, 7, 1, tzinfo=timezone.utc),
        end=datetime(2026, 7, 30, tzinfo=timezone.utc),
        resolution="weekly",
        adjustment="none",
    )

    weekly = asyncio.run(provider.get_bars(base_request))
    monthly = asyncio.run(
        provider.get_bars(
            BarsRequest(
                instrument_id=base_request.instrument_id,
                start=base_request.start,
                end=base_request.end,
                resolution="monthly",
                adjustment=base_request.adjustment,
            )
        )
    )

    assert len(weekly.bars) == 5
    assert weekly.bars[0].open_price == Decimal("10.00")
    assert weekly.bars[0].high_price == Decimal("10.70")
    assert weekly.bars[0].low_price == Decimal("9.80")
    assert weekly.bars[0].close_price == Decimal("10.50")
    assert weekly.bars[0].volume == 5010
    assert len(monthly.bars) == 1
    assert monthly.bars[0].open_price == Decimal("10.00")
    assert monthly.bars[0].close_price == Decimal("13.00")
    assert monthly.bars[0].volume == 30435


def test_akshare_provider_marks_stale_cache_when_provider_degrades() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis())
    request = _request()
    fresh = asyncio.run(provider.get_bars(request))

    fake_akshare.fail_hist = True
    delayed = asyncio.run(provider.get_bars(request))
    health = asyncio.run(provider.get_health(AKSHARE_PROVIDER))

    assert fresh.is_delayed is False
    assert delayed.is_delayed is True
    assert QualityFlag.STALE_CACHE in delayed.quality_flags
    assert QualityFlag.PROVIDER_DEGRADED in delayed.quality_flags
    assert delayed.as_of == fresh.as_of
    assert health.status is DataSourceStatus.DEGRADED
    assert health.stale_cache_available is True


def test_akshare_provider_reports_unavailable_after_failure_threshold() -> None:
    fake_akshare = FakeAkshare()
    fake_akshare.fail_hist = True
    provider = _provider(fake_akshare, FakeRedis())

    with pytest.raises(RuntimeError):
        asyncio.run(provider.get_bars(_request()))
    with pytest.raises(RuntimeError):
        asyncio.run(provider.get_bars(_request()))

    health = asyncio.run(provider.get_health(AKSHARE_PROVIDER))
    assert health.status is DataSourceStatus.UNAVAILABLE
    assert health.consecutive_failures == 2


def test_market_health_api_uses_application_service() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis())
    service = MarketDataApplicationService(provider=provider, health=provider)
    app.dependency_overrides[get_market_data_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get("/market/data-sources/akshare/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "akshare"
    assert payload["status"] == "healthy"


def test_market_indicators_api_returns_backend_computed_series() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis(), max_value_bytes=65_536)
    service = MarketDataApplicationService(provider=provider, health=provider)
    app.dependency_overrides[get_market_data_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get(
            "/market/indicators",
            params={
                "instrument_id": "CN_A:000001",
                "start": "2026-07-01T00:00:00Z",
                "end": "2026-07-30T00:00:00Z",
                "resolution": "daily",
                "adjustment": "none",
                "sma_period": 5,
                "ema_period": 6,
                "macd_fast_period": 3,
                "macd_slow_period": 8,
                "macd_signal_period": 4,
                "rsi_period": 5,
                "bollinger_period": 7,
                "bollinger_multiplier": "2.5",
                "adx_period": 5,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "akshare"
    assert payload["timezone"] == "Asia/Shanghai"
    assert payload["parameters"]["sma_period"] == 5
    assert payload["parameters"]["ema_period"] == 6
    assert payload["parameters"]["macd_fast_period"] == 3
    assert payload["parameters"]["macd_slow_period"] == 8
    assert payload["parameters"]["bollinger_multiplier"] == "2.5"
    assert len(payload["points"]) == 30
    assert payload["points"][0]["sma"] is None
    assert payload["points"][-1]["sma"] is not None
    assert payload["points"][-1]["macd"] is not None


def test_market_bars_api_accepts_weekly_resolution() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis(), max_value_bytes=65_536)
    service = MarketDataApplicationService(provider=provider, health=provider)
    app.dependency_overrides[get_market_data_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get(
            "/market/bars",
            params={
                "instrument_id": "CN_A:000001",
                "start": "2026-07-01T00:00:00Z",
                "end": "2026-07-30T00:00:00Z",
                "resolution": "weekly",
                "adjustment": "none",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["resolution"] == "weekly"
    assert len(payload["bars"]) == 5
    assert payload["bars"][0]["volume"] == 5010


def test_market_quote_api_returns_backend_quote_contract() -> None:
    fake_akshare = FakeAkshare()
    provider = _provider(fake_akshare, FakeRedis())
    service = MarketDataApplicationService(provider=provider, health=provider)
    app.dependency_overrides[get_market_data_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.get("/market/quote", params={"instrument_id": "CN_A:000001"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "akshare"
    assert payload["market"] == "CN_A"
    assert payload["currency"] == "CNY"
    assert payload["last_price"] == "10.10"
    assert payload["is_delayed"] is False
