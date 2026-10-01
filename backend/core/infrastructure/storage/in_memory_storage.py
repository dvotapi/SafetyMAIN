from __future__ import annotations

from datetime import timedelta
from urllib.parse import quote, urlencode

from backend.core.contracts.clock import ClockContract
from backend.core.contracts.storage import (
    SHA256_HEADER,
    ObjectInfo,
    PresignedUpload,
)
from backend.core.infrastructure.storage.presign_rules import (
    attachment_content_disposition,
    ensure_owned_bucket,
    resolve_ttl,
    validate_upload_request,
)


class InMemoryStorage:
    """Process-local storage for tests and non-production runs without MinIO.

    Presigned URLs use the ``memory://`` scheme and are not fetchable. Tests
    simulate the client-side transfer with ``store_object``.
    """

    def __init__(
        self,
        *,
        bucket: str,
        presign_ttl_seconds: int,
        max_upload_bytes: int,
        clock: ClockContract,
    ) -> None:
        self._bucket = bucket
        self._presign_ttl_seconds = presign_ttl_seconds
        self._max_upload_bytes = max_upload_bytes
        self._clock = clock
        self._objects: dict[tuple[str, str], ObjectInfo] = {}

    @property
    def bucket(self) -> str:
        return self._bucket

    def create_upload_url(
        self,
        key: str,
        content_type: str,
        size_bytes: int,
        sha256: str,
    ) -> PresignedUpload:
        validate_upload_request(
            key=key,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=sha256,
            max_upload_bytes=self._max_upload_bytes,
        )
        return PresignedUpload(
            url=self._url(self._bucket, key, {"method": "PUT"}),
            method="PUT",
            bucket=self._bucket,
            key=key,
            expires_at=self._clock.now() + timedelta(seconds=self._presign_ttl_seconds),
            headers={"Content-Type": content_type, SHA256_HEADER: sha256},
        )

    def create_download_url(
        self,
        bucket: str,
        key: str,
        ttl: timedelta | None,
        filename: str,
        content_type: str,
    ) -> str:
        ensure_owned_bucket(bucket, self._bucket)
        return self._url(
            bucket,
            key,
            {
                "method": "GET",
                "expires_in": str(resolve_ttl(ttl, self._presign_ttl_seconds)),
                "response-content-disposition": attachment_content_disposition(filename),
                "response-content-type": content_type,
            },
        )

    def head(self, bucket: str, key: str) -> ObjectInfo | None:
        ensure_owned_bucket(bucket, self._bucket)
        return self._objects.get((bucket, key))

    def store_object(
        self,
        key: str,
        *,
        size_bytes: int,
        content_type: str | None,
        sha256: str | None,
        etag: str | None = None,
    ) -> ObjectInfo:
        """Simulate a completed client upload into the owned bucket."""

        info = ObjectInfo(
            bucket=self._bucket,
            key=key,
            size_bytes=size_bytes,
            content_type=content_type,
            sha256=sha256,
            etag=etag,
        )
        self._objects[(self._bucket, key)] = info
        return info

    @staticmethod
    def _url(bucket: str, key: str, query: dict[str, str]) -> str:
        return f"memory://{bucket}/{quote(key)}?{urlencode(query)}"
