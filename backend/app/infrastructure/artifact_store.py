from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from urllib.parse import urlparse

from minio import Minio

from app.core.config import get_settings
from app.domains.artifacts import ArtifactPayload, ArtifactReference
from app.domains.artifacts import IArtifactStore
from app.core.time import utc_now


class MinioArtifactStore(IArtifactStore):
    def __init__(self, client: Minio, bucket_name: str) -> None:
        self._client = client
        self._bucket_name = bucket_name

    @classmethod
    def from_settings(cls) -> MinioArtifactStore:
        settings = get_settings()
        endpoint = _minio_endpoint(settings.minio_endpoint)
        return cls(
            Minio(
                endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            ),
            settings.minio_bucket_lean_artifacts,
        )

    async def put(self, namespace: str, name: str, payload: ArtifactPayload) -> ArtifactReference:
        if not self._client.bucket_exists(self._bucket_name):
            self._client.make_bucket(self._bucket_name)
        object_name = f"{namespace.strip('/')}/{name.strip('/')}"
        data = BytesIO(payload.content)
        self._client.put_object(
            self._bucket_name,
            object_name,
            data,
            length=len(payload.content),
            content_type=payload.content_type,
        )
        checksum = sha256(payload.content).hexdigest()
        return ArtifactReference(
            object_uri=f"minio://{self._bucket_name}/{object_name}",
            checksum=checksum,
            content_type=payload.content_type,
            size_bytes=len(payload.content),
            created_at=utc_now(),
        )

    async def get(self, reference: ArtifactReference) -> ArtifactPayload:
        bucket, object_name = _parse_minio_uri(reference.object_uri)
        response = self._client.get_object(bucket, object_name)
        try:
            content = response.read()
        finally:
            response.close()
            response.release_conn()
        checksum = sha256(content).hexdigest()
        if checksum != reference.checksum:
            raise ValueError("artifact checksum mismatch")
        return ArtifactPayload(content=content, content_type=reference.content_type)


def _minio_endpoint(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme:
        return parsed.netloc
    return value


def _parse_minio_uri(value: str) -> tuple[str, str]:
    parsed = urlparse(value)
    if parsed.scheme != "minio" or not parsed.netloc or not parsed.path:
        raise ValueError("invalid minio artifact uri")
    return parsed.netloc, parsed.path.lstrip("/")
