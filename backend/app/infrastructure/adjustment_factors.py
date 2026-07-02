from __future__ import annotations

import json
from datetime import datetime

from app.domains.artifacts import ArtifactReference, IArtifactStore
from app.domains.data_snapshots import AdjustmentFactor, DataSnapshot
from app.infrastructure.cache import RedisCache, RedisKeyDefinition
from app.infrastructure.market_snapshots import read_parquet_payload


ADJUSTMENT_FACTOR_CACHE_KEY = RedisKeyDefinition(
    namespace="market",
    name="adjustment-factors",
    ttl_seconds=86_400,
    max_value_bytes=512_000,
    freshness_seconds=86_400,
)


class AdjustmentFactorCache:
    def __init__(self, artifact_store: IArtifactStore, cache: RedisCache) -> None:
        self._artifact_store = artifact_store
        self._cache = cache

    def put_cache(self, snapshot: DataSnapshot, factors: tuple[AdjustmentFactor, ...]) -> None:
        self._cache.set_bytes(
            ADJUSTMENT_FACTOR_CACHE_KEY,
            snapshot.id,
            _encode_factors(factors),
        )

    async def get_factors(self, snapshot: DataSnapshot) -> tuple[AdjustmentFactor, ...]:
        cached = self._cache.get_bytes(ADJUSTMENT_FACTOR_CACHE_KEY, snapshot.id)
        if cached is not None and cached.is_fresh:
            return _decode_factors(cached.value)

        payload = await self._artifact_store.get(
            ArtifactReference(
                object_uri=snapshot.object_uri,
                checksum=snapshot.checksum,
                content_type="application/parquet",
                size_bytes=0,
                created_at=snapshot.created_at,
            )
        )
        table = read_parquet_payload(payload)
        factors = tuple(
            AdjustmentFactor(
                effective_date=effective_date,
                factor=str(factor),
            )
            for effective_date, factor in zip(
                table.column("effective_date").to_pylist(),
                table.column("factor").to_pylist(),
                strict=True,
            )
        )
        self.put_cache(snapshot, factors)
        return factors


def _encode_factors(factors: tuple[AdjustmentFactor, ...]) -> bytes:
    return json.dumps(
        [
            {
                "effective_date": factor.effective_date.isoformat(),
                "factor": factor.factor,
            }
            for factor in factors
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _decode_factors(value: bytes) -> tuple[AdjustmentFactor, ...]:
    payload = json.loads(value.decode("utf-8"))
    return tuple(
        AdjustmentFactor(
            effective_date=datetime.fromisoformat(record["effective_date"]),
            factor=record["factor"],
        )
        for record in payload
    )

