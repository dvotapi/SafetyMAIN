from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from botocore.stub import Stubber

from backend.core.contracts.storage import StorageContract, StorageRequestRejectedError
from backend.core.infrastructure.storage.s3_storage import S3Storage

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
SHA256 = "ab" * 32
BUCKET = "safetymain-documents"
KEY = "org-1/compliance_document/doc-1/upload-1/instruction.pdf"


class FixedClock:
    def now(self) -> datetime:
        return NOW


def _storage(**overrides: object) -> S3Storage:
    values: dict[str, object] = {
        "bucket": BUCKET,
        "endpoint_url": "http://localhost:9000",
        "region": "us-east-1",
        "access_key": "minio-access",
        "secret_key": "minio-secret",
        "presign_ttl_seconds": 900,
        "max_upload_bytes": 1024,
        "clock": FixedClock(),
    }
    values.update(overrides)
    return S3Storage(**values)  # type: ignore[arg-type]


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def test_s3_storage_satisfies_contract() -> None:
    storage: StorageContract = _storage()

    assert storage is not None


def test_upload_url_signs_content_type_length_and_sha256() -> None:
    upload = _storage().create_upload_url(KEY, "application/pdf", 512, SHA256)

    parsed = urlparse(upload.url)
    query = _query(upload.url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "localhost:9000"
    assert unquote(parsed.path) == f"/{BUCKET}/{KEY}"
    assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
    assert query["X-Amz-Expires"] == ["900"]
    assert query["X-Amz-SignedHeaders"][0].split(";") == [
        "content-length",
        "content-type",
        "host",
        "x-amz-meta-sha256",
    ]
    assert upload.method == "PUT"
    assert upload.bucket == BUCKET
    assert upload.key == KEY
    assert upload.expires_at == NOW + timedelta(seconds=900)
    assert upload.headers == {
        "Content-Type": "application/pdf",
        "x-amz-meta-sha256": SHA256,
    }


def test_upload_url_contains_no_checksum_parameters() -> None:
    upload = _storage().create_upload_url(KEY, "application/pdf", 512, SHA256)

    assert not any("checksum" in name.lower() for name in _query(upload.url))


def test_upload_url_rejects_size_above_limit_before_signing() -> None:
    with pytest.raises(StorageRequestRejectedError, match="limit"):
        _storage().create_upload_url(KEY, "application/pdf", 1025, SHA256)


@pytest.mark.parametrize(
    ("key", "content_type", "size_bytes", "sha256"),
    [
        ("", "application/pdf", 1, SHA256),
        ("/absolute", "application/pdf", 1, SHA256),
        ("line\nbreak", "application/pdf", 1, SHA256),
        (KEY, " ", 1, SHA256),
        (KEY, "application/pdf\r\nX-Injected: 1", 1, SHA256),
        (KEY, "application/pdf", 0, SHA256),
        (KEY, "application/pdf", 1, "AB" * 32),
        (KEY, "application/pdf", 1, "ab" * 31),
    ],
)
def test_upload_url_rejects_malformed_requests(
    key: str, content_type: str, size_bytes: int, sha256: str
) -> None:
    with pytest.raises(StorageRequestRejectedError):
        _storage().create_upload_url(key, content_type, size_bytes, sha256)


def test_download_url_forces_attachment_with_rfc5987_filename() -> None:
    url = _storage().create_download_url(
        BUCKET, KEY, None, "Инструкция \"ОТ\".pdf", "application/pdf"
    )

    query = _query(url)
    disposition = query["response-content-disposition"][0]
    assert disposition.startswith("attachment; ")
    assert 'filename="__________ ____.pdf"' in disposition
    assert (
        "filename*=UTF-8''%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BA%D1%86%D0%B8%D1%8F"
        "%20%22%D0%9E%D0%A2%22.pdf"
    ) in disposition
    assert query["response-content-type"] == ["application/pdf"]
    assert query["X-Amz-Expires"] == ["900"]
    assert query["X-Amz-SignedHeaders"] == ["host"]


def test_download_url_honours_explicit_ttl() -> None:
    url = _storage().create_download_url(
        BUCKET, KEY, timedelta(minutes=2), "a.pdf", "application/pdf"
    )

    assert _query(url)["X-Amz-Expires"] == ["120"]


def test_download_url_rejects_foreign_bucket() -> None:
    with pytest.raises(StorageRequestRejectedError):
        _storage().create_download_url("complex-hr-docs", KEY, None, "a.pdf", "application/pdf")


def test_head_returns_object_info() -> None:
    storage = _storage()
    with Stubber(storage._client) as stubber:
        stubber.add_response(
            "head_object",
            {
                "ContentLength": 512,
                "ContentType": "application/pdf",
                "ETag": '"etag-1"',
                "Metadata": {"sha256": SHA256},
            },
            {"Bucket": BUCKET, "Key": KEY},
        )

        info = storage.head(BUCKET, KEY)

    assert info is not None
    assert info.bucket == BUCKET
    assert info.key == KEY
    assert info.size_bytes == 512
    assert info.content_type == "application/pdf"
    assert info.sha256 == SHA256
    assert info.etag == "etag-1"


def test_head_returns_none_for_missing_object() -> None:
    storage = _storage()
    with Stubber(storage._client) as stubber:
        stubber.add_client_error(
            "head_object",
            service_error_code="404",
            http_status_code=404,
            expected_params={"Bucket": BUCKET, "Key": KEY},
        )

        assert storage.head(BUCKET, KEY) is None


def test_head_propagates_other_storage_errors() -> None:
    storage = _storage()
    with Stubber(storage._client) as stubber:
        stubber.add_client_error(
            "head_object",
            service_error_code="403",
            http_status_code=403,
            expected_params={"Bucket": BUCKET, "Key": KEY},
        )

        with pytest.raises(Exception, match="403"):
            storage.head(BUCKET, KEY)


def test_head_rejects_foreign_bucket() -> None:
    with pytest.raises(StorageRequestRejectedError):
        _storage().head("complex-hr-docs", KEY)
