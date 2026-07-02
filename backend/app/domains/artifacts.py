from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    object_uri: str
    checksum: str
    content_type: str
    size_bytes: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ArtifactPayload:
    content: bytes
    content_type: str


class IArtifactStore(Protocol):
    async def put(self, namespace: str, name: str, payload: ArtifactPayload) -> ArtifactReference: ...

    async def get(self, reference: ArtifactReference) -> ArtifactPayload: ...

