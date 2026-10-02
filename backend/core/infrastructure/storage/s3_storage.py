from __future__ import annotations

from datetime import timedelta

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from backend.core.contracts.clock import ClockContract
from backend.core.contracts.storage import (
    SHA256_HEADER,
    SHA256_METADATA_KEY,
    ObjectInfo,
    PresignedUpload,
)
from backend.core.infrastructure.storage.presign_rules import (
    attachment_content_disposition,
    ensure_owned_bucket,
    resolve_ttl,
    validate_object_reference,
    validate_upload_request,
)

_NOT_FOUND_CODES = frozenset({"404", "NoSuchKey", "NotFound"})


class S3Storage:
    """S3-compatible storage adapter (MinIO in development, Yandex Object Storage
    in production), using SigV4 presigned URLs.

    Creating the adapter performs no network I/O. The endpoint must be reachable
    by browsers, because presigned URLs are signed for that host.
    """

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        region: str,
        access_key: str | None,
        secret_key: str | None,
        presign_ttl_seconds: int,
        max_upload_bytes: int,
        clock: ClockContract,
    ) -> None:
        self._bucket = bucket
        self._presign_ttl_seconds = presign_ttl_seconds
        self._max_upload_bytes = max_upload_bytes
        self._clock = clock
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

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
        issued_at = self._clock.now()
        url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
                "ContentLength": size_bytes,
                "Metadata": {SHA256_METADATA_KEY: sha256},
            },
            ExpiresIn=self._presign_ttl_seconds,
            HttpMethod="PUT",
        )
        return PresignedUpload(
            url=url,
            method="PUT",
            bucket=self._bucket,
            key=key,
            expires_at=issued_at + timedelta(seconds=self._presign_ttl_seconds),
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
        validate_object_reference(key=key, content_type=content_type)
        return self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ResponseContentDisposition": attachment_content_disposition(filename),
                "ResponseContentType": content_type,
            },
            ExpiresIn=resolve_ttl(ttl, self._presign_ttl_seconds),
            HttpMethod="GET",
        )

    def head(self, bucket: str, key: str) -> ObjectInfo | None:
        ensure_owned_bucket(bucket, self._bucket)
        try:
            response = self._client.head_object(Bucket=bucket, Key=key)
        except ClientError as error:
            if str(error.response.get("Error", {}).get("Code")) in _NOT_FOUND_CODES:
                return None
            raise
        etag = response.get("ETag")
        return ObjectInfo(
            bucket=bucket,
            key=key,
            size_bytes=int(response["ContentLength"]),
            content_type=response.get("ContentType"),
            sha256=response.get("Metadata", {}).get(SHA256_METADATA_KEY),
            etag=etag.strip('"') if etag else None,
        )
