from __future__ import annotations

import re
from datetime import timedelta
from urllib.parse import quote

from backend.core.contracts.storage import StorageRequestRejectedError

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
# RFC 5987 attr-char minus ALPHA / DIGIT and the characters ``quote`` keeps anyway.
_RFC5987_SAFE = "!#$&+^`|"
# SigV4 presigned URLs cannot outlive seven days.
MAX_PRESIGN_TTL_SECONDS = 604_800


def validate_upload_request(
    *,
    key: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
    max_upload_bytes: int,
) -> None:
    """Reject upload requests that must never be signed."""

    validate_object_reference(key=key, content_type=content_type)
    if size_bytes <= 0:
        raise StorageRequestRejectedError("File size must be positive.")
    if size_bytes > max_upload_bytes:
        raise StorageRequestRejectedError("File size exceeds the upload limit.")
    if _SHA256_HEX.fullmatch(sha256) is None:
        raise StorageRequestRejectedError(
            "SHA-256 must be 64 lowercase hexadecimal characters."
        )


def validate_object_reference(*, key: str, content_type: str) -> None:
    """Reject keys and content types that must never reach a signed request."""

    if not key or key.startswith("/") or _CONTROL_CHARACTERS.search(key):
        raise StorageRequestRejectedError("Object key is malformed.")
    if not content_type.strip() or _CONTROL_CHARACTERS.search(content_type):
        raise StorageRequestRejectedError("Content type is malformed.")


def ensure_owned_bucket(bucket: str, owned_bucket: str) -> None:
    """Only the SafetyMAIN-owned bucket is reachable with the primary credential."""

    if bucket != owned_bucket:
        raise StorageRequestRejectedError("Bucket is not served by this storage.")


def resolve_ttl(ttl: timedelta | None, default_ttl_seconds: int) -> int:
    if ttl is None:
        return default_ttl_seconds
    seconds = int(ttl.total_seconds())
    if not 0 < seconds <= MAX_PRESIGN_TTL_SECONDS:
        raise StorageRequestRejectedError(
            f"Presign lifetime must be between 1 and {MAX_PRESIGN_TTL_SECONDS} seconds."
        )
    return seconds


def attachment_content_disposition(filename: str) -> str:
    """Build ``attachment`` with an ASCII fallback and an RFC 5987 UTF-8 name."""

    cleaned = _CONTROL_CHARACTERS.sub("", filename).strip() or "download"
    fallback = "".join(
        character if character.isascii() and character not in '"\\' else "_"
        for character in cleaned
    )
    encoded = quote(cleaned, safe=_RFC5987_SAFE)
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
