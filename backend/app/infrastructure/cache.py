from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from redis import Redis

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class RedisKeyDefinition:
    namespace: str
    name: str
    ttl_seconds: int
    max_value_bytes: int
    freshness_seconds: int

    def key(self, identity: str) -> str:
        return f"quanttrade:{self.namespace}:{self.name}:{identity}"


@dataclass(frozen=True, slots=True)
class CachedValue:
    value: bytes
    stored_at: datetime
    is_fresh: bool


class RedisCache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    @classmethod
    def from_settings(cls) -> RedisCache:
        return cls(Redis.from_url(get_settings().redis_url))

    def set_bytes(self, definition: RedisKeyDefinition, identity: str, value: bytes) -> str:
        if len(value) > definition.max_value_bytes:
            raise ValueError("redis value exceeds declared key capacity")
        key = definition.key(identity)
        stored_at = datetime.now(timezone.utc).isoformat()
        self._client.hset(key, mapping={"value": value, "stored_at": stored_at.encode("utf-8")})
        self._client.expire(key, definition.ttl_seconds)
        return key

    def get_bytes(self, definition: RedisKeyDefinition, identity: str) -> CachedValue | None:
        key = definition.key(identity)
        payload = self._client.hgetall(key)
        if not payload:
            return None
        stored_at_raw = _as_bytes(payload[b"stored_at"]).decode("utf-8")
        stored_at = datetime.fromisoformat(stored_at_raw)
        age_seconds = (datetime.now(timezone.utc) - stored_at).total_seconds()
        return CachedValue(
            value=_as_bytes(payload[b"value"]),
            stored_at=stored_at,
            is_fresh=age_seconds <= definition.freshness_seconds,
        )


JOB_PROGRESS_KEY = RedisKeyDefinition(
    namespace="jobs",
    name="progress",
    ttl_seconds=86_400,
    max_value_bytes=4096,
    freshness_seconds=300,
)


def _as_bytes(value: bytes | str) -> bytes:
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")
