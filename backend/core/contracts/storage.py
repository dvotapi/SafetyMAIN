from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol

SHA256_METADATA_KEY = "sha256"
SHA256_HEADER = f"x-amz-meta-{SHA256_METADATA_KEY}"


class StorageRequestRejectedError(ValueError):
    """Raised when a storage request violates the configured storage rules."""


@dataclass(frozen=True, slots=True)
class PresignedUpload:
    """Presigned direct upload of one object into the SafetyMAIN-owned bucket.

    ``headers`` lists the headers the client must send verbatim. The signed
    ``Content-Length`` is not listed: HTTP clients (browsers included) derive it
    from the request body, which must be exactly ``size_bytes`` long.
    """

    url: str
    method: str
    bucket: str
    key: str
    expires_at: datetime
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ObjectInfo:
    """Metadata of a stored object as reported by object storage."""

    bucket: str
    key: str
    size_bytes: int
    content_type: str | None
    sha256: str | None
    etag: str | None


class StorageContract(Protocol):
    """Object storage port built around presigned access (ADR-0006).

    File bytes never pass through the API process. The port offers no physical
    deletion.
    """

    @property
    def bucket(self) -> str:
        """Name of the SafetyMAIN-owned bucket this adapter serves."""
        ...

    def create_upload_url(
        self,
        key: str,
        content_type: str,
        size_bytes: int,
        sha256: str,
    ) -> PresignedUpload:
        """Sign a PUT that pins ``Content-Type``, ``Content-Length`` and the
        SHA-256 metadata. Raises ``StorageRequestRejectedError`` when the size
        exceeds the configured limit or an argument is malformed."""
        ...

    def create_download_url(
        self,
        bucket: str,
        key: str,
        ttl: timedelta | None,
        filename: str,
        content_type: str,
    ) -> str:
        """Sign a GET that forces an attachment download with ``filename``.

        ``ttl=None`` uses the configured presign lifetime.
        """
        ...

    def head(self, bucket: str, key: str) -> ObjectInfo | None:
        """Return object metadata, or ``None`` when the object does not exist."""
        ...
