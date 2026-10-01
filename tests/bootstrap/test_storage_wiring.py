from __future__ import annotations

import pytest

from backend.bootstrap.container import create_container
from backend.bootstrap.security_validation import SecurityConfigurationError
from backend.bootstrap.settings import AppSettings
from backend.core.infrastructure.storage.in_memory_storage import InMemoryStorage
from backend.core.infrastructure.storage.s3_storage import S3Storage


def test_development_without_bucket_uses_in_memory_storage() -> None:
    container = create_container(AppSettings())

    assert isinstance(container.storage, InMemoryStorage)


def test_configured_bucket_uses_s3_storage_without_network() -> None:
    container = create_container(
        AppSettings(
            storage_endpoint_url="http://localhost:9000",
            storage_bucket="safetymain-documents",
            storage_access_key="minio-access",
            storage_secret_key="minio-secret",
        )
    )

    assert isinstance(container.storage, S3Storage)
    assert container.storage.bucket == "safetymain-documents"


def test_production_never_falls_back_to_in_memory_storage() -> None:
    settings = AppSettings(
        app_env="production",
        database_url="postgresql+psycopg://user:pass@localhost:5432/safetymain",
        jwt_secret_key="production-secret-key-with-sufficient-length",
        jwt_issuer="safetymain-prod",
        auth_enforcement=True,
    )

    with pytest.raises(SecurityConfigurationError, match="STORAGE_BUCKET"):
        create_container(settings)
