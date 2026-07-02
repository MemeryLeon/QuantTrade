from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.domains.artifacts import ArtifactReference
from app.domains.data_snapshots import AdjustmentFactor, CompanyAction
from app.domains.indicators import adx, bollinger_bands, ema, macd, rsi, sma
from app.domains.market import Bar
from app.infrastructure.adjustment_factors import AdjustmentFactorCache
from app.infrastructure.artifact_store import MinioArtifactStore
from app.infrastructure.cache import RedisCache
from app.infrastructure.market_snapshots import (
    ADJUSTMENT_FACTOR_SCHEMA_VERSION,
    COMPANY_ACTION_SCHEMA_VERSION,
    OHLCV_SCHEMA_VERSION,
    MarketSnapshotStore,
    read_parquet_payload,
)


@dataclass(slots=True)
class FakeMinioResponse:
    content: bytes

    def read(self) -> bytes:
        return self.content

    def close(self) -> None:
        pass

    def release_conn(self) -> None:
        pass


class FakeMinio:
    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], bytes] = {}

    def bucket_exists(self, bucket_name: str) -> bool:
        return bucket_name in self.buckets

    def make_bucket(self, bucket_name: str) -> None:
        self.buckets.add(bucket_name)

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data,
        length: int,
        content_type: str,
    ) -> None:
        self.objects[(bucket_name, object_name)] = data.read(length)

    def get_object(self, bucket_name: str, object_name: str) -> FakeMinioResponse:
        return FakeMinioResponse(self.objects[(bucket_name, object_name)])


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


def test_market_snapshots_store_parquet_artifacts_and_metadata() -> None:
    artifact_store = MinioArtifactStore(FakeMinio(), "market-data")  # type: ignore[arg-type]
    snapshot_store = MarketSnapshotStore(artifact_store)
    bars = (
        Bar(
            observed_at=datetime(2026, 7, 1, 7, 0, tzinfo=timezone.utc),
            open_price=Decimal("10.0000"),
            high_price=Decimal("10.2000"),
            low_price=Decimal("9.9000"),
            close_price=Decimal("10.1000"),
            volume=1000,
            quality_flags=(),
        ),
    )

    snapshot = asyncio.run(
        snapshot_store.create_ohlcv_snapshot(
            source_id="akshare",
            market="CN_A",
            instrument_scope="CN_A:000001",
            resolution="daily",
            adjustment="none",
            timezone_name="Asia/Shanghai",
            calendar_version="akshare-sina-trade-date-v1",
            bars=bars,
        )
    )
    payload = asyncio.run(
        artifact_store.get(
            ArtifactReference(
                object_uri=snapshot.object_uri,
                checksum=snapshot.checksum,
                content_type="application/parquet",
                size_bytes=0,
                created_at=snapshot.created_at,
            )
        )
    )
    table = read_parquet_payload(payload)

    assert snapshot.schema_version == OHLCV_SCHEMA_VERSION
    assert snapshot.row_count == 1
    assert snapshot.object_uri.endswith("/ohlcv.parquet")
    assert table.schema.field("observed_at").type.tz == "UTC"
    assert table.column("close_price").to_pylist() == [Decimal("10.1000")]
    assert table.column("volume").to_pylist() == [1000]


def test_adjustment_factors_recover_from_minio_when_redis_is_lost() -> None:
    artifact_store = MinioArtifactStore(FakeMinio(), "market-data")  # type: ignore[arg-type]
    snapshot_store = MarketSnapshotStore(artifact_store)
    factors = (
        AdjustmentFactor(
            effective_date=datetime(2026, 7, 1, 7, 0, tzinfo=timezone.utc),
            factor="1.00000000",
        ),
    )
    snapshot = asyncio.run(
        snapshot_store.create_adjustment_factor_snapshot(
            source_id="akshare",
            market="CN_A",
            instrument_scope="CN_A:000001",
            timezone_name="Asia/Shanghai",
            calendar_version="akshare-sina-trade-date-v1",
            factors=factors,
        )
    )
    initial_cache = AdjustmentFactorCache(
        artifact_store,
        RedisCache(FakeRedis()),  # type: ignore[arg-type]
    )
    initial_cache.put_cache(snapshot, factors)

    restored_cache = AdjustmentFactorCache(
        artifact_store,
        RedisCache(FakeRedis()),  # type: ignore[arg-type]
    )
    restored = asyncio.run(restored_cache.get_factors(snapshot))

    assert snapshot.schema_version == ADJUSTMENT_FACTOR_SCHEMA_VERSION
    assert restored[0].effective_date == factors[0].effective_date
    assert restored[0].factor == "1.00000000"


def test_company_actions_are_stored_as_parquet_artifacts() -> None:
    artifact_store = MinioArtifactStore(FakeMinio(), "market-data")  # type: ignore[arg-type]
    snapshot_store = MarketSnapshotStore(artifact_store)
    actions = (
        CompanyAction(
            effective_date=datetime(2026, 7, 1, 7, 0, tzinfo=timezone.utc),
            action_type="cash_dividend",
            description="fixture dividend",
        ),
    )

    snapshot = asyncio.run(
        snapshot_store.create_company_action_snapshot(
            source_id="akshare",
            market="CN_A",
            instrument_scope="CN_A:000001",
            timezone_name="Asia/Shanghai",
            calendar_version="akshare-sina-trade-date-v1",
            actions=actions,
        )
    )

    assert snapshot.schema_version == COMPANY_ACTION_SCHEMA_VERSION
    assert snapshot.row_count == 1
    assert snapshot.object_uri.endswith("/company-actions.parquet")


def test_indicator_golden_sample() -> None:
    closes = tuple(
        Decimal(str(value))
        for value in [
            10,
            10.5,
            10.2,
            10.8,
            11,
            10.7,
            11.3,
            11.8,
            11.5,
            12,
            12.4,
            12.1,
            12.8,
            13,
            12.7,
            13.2,
            13.6,
            13.4,
            13.9,
            14.2,
            14.0,
            14.5,
            14.8,
            14.6,
            15.1,
            15.4,
            15.2,
            15.8,
            16,
            15.7,
        ]
    )
    highs = tuple(value + Decimal("0.3") for value in closes)
    lows = tuple(value - Decimal("0.4") for value in closes)
    macd_result = macd(closes, fast_period=3, slow_period=6, signal_period=3)
    bands = bollinger_bands(closes, period=5, multiplier=Decimal("2"))

    assert _fmt(sma(closes, 5)[-5:]) == [
        "14.8800",
        "15.0200",
        "15.2200",
        "15.5000",
        "15.6200",
    ]
    assert _fmt(ema(closes, 5)[-5:]) == [
        "14.8831",
        "14.9887",
        "15.2592",
        "15.5061",
        "15.5707",
    ]
    assert _fmt(macd_result.macd[-5:]) == ["0.3402", "0.2614", "0.3245", "0.3435", "0.2369"]
    assert _fmt(macd_result.signal[-5:]) == ["0.3197", "0.2905", "0.3075", "0.3255", "0.2812"]
    assert _fmt(macd_result.histogram[-5:]) == [
        "0.0205",
        "-0.0292",
        "0.0170",
        "0.0180",
        "-0.0443",
    ]
    assert _fmt(rsi(closes, 5)[-5:]) == ["83.9423", "73.4075", "81.9176", "84.0450", "68.8556"]
    assert _fmt(bands.middle[-3:]) == ["15.2200", "15.5000", "15.6200"]
    assert _fmt(bands.upper[-3:]) == ["16.0038", "16.1928", "16.1913"]
    assert _fmt(bands.lower[-3:]) == ["14.4362", "14.8072", "15.0487"]
    assert _fmt(adx(highs, lows, closes, 5)[-5:]) == [
        "58.4149",
        "56.0949",
        "57.6430",
        "59.7324",
        "55.3281",
    ]


def _fmt(values: tuple[Decimal | None, ...]) -> list[str | None]:
    quant = Decimal("0.0001")
    return [
        None if value is None else str(value.quantize(quant, rounding=ROUND_HALF_UP))
        for value in values
    ]

