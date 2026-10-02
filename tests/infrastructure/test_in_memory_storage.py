from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from backend.core.contracts.storage import StorageContract, StorageRequestRejectedError
from backend.core.infrastructure.storage.in_memory_storage import InMemoryStorage

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
SHA256 = "cd" * 32
BUCKET = "safetymain-test"
KEY = "org-1/compliance_document/doc-1/upload-1/act.pdf"


class FixedClock:
    def now(self) -> datetime:
        return NOW


def _storage() -> InMemoryStorage:
    return InMemoryStorage(
        bucket=BUCKET,
        presign_ttl_seconds=300,
        max_upload_bytes=1024,
        clock=FixedClock(),
    )


def test_in_memory_storage_satisfies_contract() -> None:
    storage: StorageContract = _storage()

    assert storage is not None


def test_upload_url_returns_presigned_upload() -> None:
    upload = _storage().create_upload_url(KEY, "application/pdf", 100, SHA256)

    assert upload.url.startswith(f"memory://{BUCKET}/")
    assert upload.method == "PUT"
    assert upload.bucket == BUCKET
    assert upload.key == KEY
    assert upload.expires_at == NOW + timedelta(seconds=300)
    assert upload.headers == {
        "Content-Type": "application/pdf",
        "x-amz-meta-sha256": SHA256,
    }


def test_upload_url_does_not_create_object() -> None:
    storage = _storage()
    storage.create_upload_url(KEY, "application/pdf", 100, SHA256)

    assert storage.head(BUCKET, KEY) is None


def test_upload_url_enforces_same_rules_as_s3_adapter() -> None:
    storage = _storage()

    with pytest.raises(StorageRequestRejectedError, match="limit"):
        storage.create_upload_url(KEY, "application/pdf", 1025, SHA256)
    with pytest.raises(StorageRequestRejectedError):
        storage.create_upload_url(KEY, "application/pdf", 10, "not-a-hash")


def test_head_returns_stored_object() -> None:
    storage = _storage()
    stored = storage.store_object(
        KEY, size_bytes=100, content_type="application/pdf", sha256=SHA256, etag="e1"
    )

    assert storage.head(BUCKET, KEY) == stored
    assert stored.bucket == BUCKET
    assert stored.size_bytes == 100
    assert stored.sha256 == SHA256


def test_head_returns_none_for_missing_object() -> None:
    assert _storage().head(BUCKET, "missing") is None


def test_download_url_carries_attachment_disposition_and_ttl() -> None:
    url = _storage().create_download_url(
        BUCKET, KEY, timedelta(seconds=60), "Приказ.pdf", "application/pdf"
    )

    query = parse_qs(urlparse(url).query)
    assert query["expires_in"] == ["60"]
    assert query["response-content-type"] == ["application/pdf"]
    disposition = query["response-content-disposition"][0]
    assert disposition.startswith('attachment; filename="______.pdf"; ')
    assert "filename*=UTF-8''%D0%9F%D1%80%D0%B8%D0%BA%D0%B0%D0%B7.pdf" in disposition


def test_download_url_rejects_non_positive_ttl() -> None:
    with pytest.raises(StorageRequestRejectedError):
        _storage().create_download_url(BUCKET, KEY, timedelta(0), "a.pdf", "application/pdf")


def test_foreign_bucket_is_rejected() -> None:
    storage = _storage()

    with pytest.raises(StorageRequestRejectedError):
        storage.head("complex-hr-docs", KEY)
    with pytest.raises(StorageRequestRejectedError):
        storage.create_download_url("complex-hr-docs", KEY, None, "a.pdf", "application/pdf")


def test_download_url_validates_reference_and_ttl_like_s3_adapter() -> None:
    storage = _storage()

    with pytest.raises(StorageRequestRejectedError):
        storage.create_download_url(BUCKET, "", None, "a.pdf", "application/pdf")
    with pytest.raises(StorageRequestRejectedError):
        storage.create_download_url(BUCKET, KEY, None, "a.pdf", "text/plain\nX: 1")
    with pytest.raises(StorageRequestRejectedError):
        storage.create_download_url(
            BUCKET, KEY, timedelta(days=8), "a.pdf", "application/pdf"
        )
