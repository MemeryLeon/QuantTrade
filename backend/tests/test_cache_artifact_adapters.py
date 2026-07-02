from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.domains.artifacts import ArtifactPayload
from app.infrastructure.artifact_store import MinioArtifactStore
from app.infrastructure.cache import RedisCache, RedisKeyDefinition


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


def test_redis_cache_requires_declared_capacity_ttl_and_freshness() -> None:
    fake = FakeRedis()
    cache = RedisCache(fake)  # type: ignore[arg-type]
    definition = RedisKeyDefinition(
        namespace="jobs",
        name="progress",
        ttl_seconds=60,
        max_value_bytes=16,
        freshness_seconds=30,
    )

    key = cache.set_bytes(definition, "job-1", b"running")
    restored = cache.get_bytes(definition, "job-1")

    assert key == "quanttrade:jobs:progress:job-1"
    assert fake.expirations[key] == 60
    assert restored is not None
    assert restored.value == b"running"
    assert restored.is_fresh is True


def test_redis_cache_rejects_values_over_declared_capacity() -> None:
    cache = RedisCache(FakeRedis())  # type: ignore[arg-type]
    definition = RedisKeyDefinition(
        namespace="jobs",
        name="progress",
        ttl_seconds=60,
        max_value_bytes=2,
        freshness_seconds=30,
    )

    try:
        cache.set_bytes(definition, "job-1", b"too-large")
    except ValueError as exc:
        assert "capacity" in str(exc)
    else:
        raise AssertionError("expected capacity error")


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


def test_minio_artifact_store_round_trip_checks_checksum() -> None:
    fake = FakeMinio()
    store = MinioArtifactStore(fake, "artifacts")  # type: ignore[arg-type]

    reference = asyncio.run(
        store.put(
            namespace="mock",
            name="result.json",
            payload=ArtifactPayload(content=b'{"ok":true}', content_type="application/json"),
        )
    )
    restored = asyncio.run(store.get(reference))

    assert reference.object_uri == "minio://artifacts/mock/result.json"
    assert restored.content == b'{"ok":true}'
    assert restored.content_type == "application/json"

