from __future__ import annotations

import logging
from uuid import uuid4

import pytest

from backend.api.app import create_app
from backend.bootstrap.container import create_container
from backend.bootstrap.security_validation import (
    SecurityConfigurationError,
    validate_security_configuration,
)
from backend.bootstrap.settings import AppSettings, load_settings
from backend.bootstrap.startup_logging import log_security_configuration


def _production_settings(**overrides: object) -> AppSettings:
    values: dict[str, object] = {
        "app_env": "production",
        "database_url": "postgresql+psycopg://user:pass@localhost:5432/safetymain",
        "jwt_secret_key": "production-secret-key-with-sufficient-length",
        "jwt_algorithm": "HS256",
        "jwt_access_token_ttl_seconds": 3600,
        "jwt_refresh_token_ttl_seconds": 604800,
        "jwt_issuer": "safetymain-prod",
        "auth_enforcement": True,
        "storage_endpoint_url": "https://storage.yandexcloud.net",
        "storage_bucket": "safetymain-documents",
        "storage_access_key": "production-storage-access-key",
        "storage_secret_key": "production-storage-secret-key",
    }
    values.update(overrides)
    return AppSettings(**values)


def test_development_defaults_pass_validation() -> None:
    settings = load_settings(environment={})

    validate_security_configuration(settings)


def test_production_configuration_passes_validation() -> None:
    validate_security_configuration(_production_settings())


def test_production_rejects_development_jwt_secret() -> None:
    with pytest.raises(SecurityConfigurationError, match="placeholder"):
        validate_security_configuration(
            _production_settings(jwt_secret_key="dev-insecure-change-me")
        )


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(SecurityConfigurationError, match="32 characters"):
        validate_security_configuration(_production_settings(jwt_secret_key="short-secret"))


def test_production_rejects_missing_database_url() -> None:
    with pytest.raises(SecurityConfigurationError, match="DATABASE_URL"):
        validate_security_configuration(_production_settings(database_url=None))


def test_production_rejects_disabled_auth_enforcement() -> None:
    with pytest.raises(SecurityConfigurationError, match="AUTH_ENFORCEMENT"):
        validate_security_configuration(_production_settings(auth_enforcement=False))


def test_production_requires_configured_issuer() -> None:
    with pytest.raises(SecurityConfigurationError, match="JWT_ISSUER"):
        validate_security_configuration(_production_settings(jwt_issuer=None))


def test_rejects_unsupported_jwt_algorithm() -> None:
    settings = AppSettings(jwt_algorithm="RS256")

    with pytest.raises(SecurityConfigurationError, match="JWT_ALGORITHM"):
        validate_security_configuration(settings)


def test_rejects_empty_jwt_algorithm() -> None:
    settings = AppSettings(jwt_algorithm="   ")

    with pytest.raises(SecurityConfigurationError, match="JWT_ALGORITHM"):
        validate_security_configuration(settings)


def test_rejects_refresh_ttl_not_greater_than_access_ttl() -> None:
    settings = AppSettings(
        jwt_access_token_ttl_seconds=3600,
        jwt_refresh_token_ttl_seconds=3600,
    )

    with pytest.raises(SecurityConfigurationError, match="greater than"):
        validate_security_configuration(settings)


def test_load_settings_rejects_refresh_ttl_not_greater_than_access_ttl() -> None:
    with pytest.raises(SecurityConfigurationError, match="greater than"):
        load_settings(
            environment={
                "JWT_ACCESS_TOKEN_TTL_SECONDS": "3600",
                "JWT_REFRESH_TOKEN_TTL_SECONDS": "3600",
            }
        )


def test_rejects_whitespace_only_jwt_issuer() -> None:
    settings = AppSettings(jwt_issuer="   ")

    with pytest.raises(SecurityConfigurationError, match="JWT_ISSUER"):
        validate_security_configuration(settings)


def test_create_container_fails_before_dependency_construction() -> None:
    with pytest.raises(SecurityConfigurationError):
        create_container(_production_settings(jwt_secret_key="dev-insecure-change-me"))


def test_create_app_fails_with_invalid_production_configuration() -> None:
    with pytest.raises(SecurityConfigurationError):
        create_app(settings=_production_settings(jwt_secret_key="changeme"))


def test_create_app_succeeds_with_valid_production_configuration() -> None:
    application = create_app(settings=_production_settings())

    assert application.state.settings.app_env == "production"


def test_startup_logging_does_not_expose_sensitive_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import backend.bootstrap.startup_logging as startup_logging

    startup_logging._LOGGED_SECURITY_CONFIGURATION = False
    secret = f"production-secret-key-{uuid4()}"
    settings = _production_settings(jwt_secret_key=secret)

    with caplog.at_level(logging.INFO):
        log_security_configuration(settings)

    logged = caplog.text
    assert secret not in logged
    assert "jwt_algorithm=HS256" in logged
    assert "auth_enforcement=True" in logged


def test_load_settings_storage_defaults() -> None:
    settings = load_settings(environment={})

    assert settings.storage_bucket is None
    assert settings.storage_endpoint_url is None
    assert settings.storage_region == "us-east-1"
    assert settings.storage_presign_ttl_seconds == 900
    assert settings.storage_max_upload_bytes == 50 * 1024 * 1024
    assert settings.storage_external_access_key is None
    assert settings.storage_external_secret_key is None


def test_load_settings_reads_storage_environment() -> None:
    settings = load_settings(
        environment={
            "STORAGE_ENDPOINT_URL": " https://storage.yandexcloud.net ",
            "STORAGE_REGION": "ru-central1",
            "STORAGE_BUCKET": "safetymain-documents",
            "STORAGE_ACCESS_KEY": "access",
            "STORAGE_SECRET_KEY": "secret",
            "STORAGE_PRESIGN_TTL_SECONDS": "600",
            "STORAGE_MAX_UPLOAD_BYTES": "1048576",
            "STORAGE_EXTERNAL_ACCESS_KEY": "external-access",
            "STORAGE_EXTERNAL_SECRET_KEY": "external-secret",
        }
    )

    assert settings.storage_endpoint_url == "https://storage.yandexcloud.net"
    assert settings.storage_region == "ru-central1"
    assert settings.storage_bucket == "safetymain-documents"
    assert settings.storage_access_key == "access"
    assert settings.storage_secret_key == "secret"
    assert settings.storage_presign_ttl_seconds == 600
    assert settings.storage_max_upload_bytes == 1_048_576
    assert settings.storage_external_access_key == "external-access"
    assert settings.storage_external_secret_key == "external-secret"


def test_load_settings_treats_blank_storage_values_as_unset() -> None:
    settings = load_settings(
        environment={"STORAGE_BUCKET": "  ", "STORAGE_ACCESS_KEY": "", "STORAGE_REGION": " "}
    )

    assert settings.storage_bucket is None
    assert settings.storage_access_key is None
    assert settings.storage_region == "us-east-1"


def test_load_settings_rejects_non_positive_max_upload_bytes() -> None:
    with pytest.raises(ValueError, match="STORAGE_MAX_UPLOAD_BYTES"):
        load_settings(environment={"STORAGE_MAX_UPLOAD_BYTES": "0"})


@pytest.mark.parametrize("ttl", [59, 604_801])
def test_rejects_presign_ttl_outside_bounds(ttl: int) -> None:
    with pytest.raises(SecurityConfigurationError, match="STORAGE_PRESIGN_TTL_SECONDS"):
        validate_security_configuration(AppSettings(storage_presign_ttl_seconds=ttl))


def test_rejects_max_upload_bytes_above_single_put_limit() -> None:
    with pytest.raises(SecurityConfigurationError, match="STORAGE_MAX_UPLOAD_BYTES"):
        validate_security_configuration(
            AppSettings(storage_max_upload_bytes=5 * 1024 * 1024 * 1024 + 1)
        )


@pytest.mark.parametrize(
    ("field", "variable"),
    [
        ("storage_bucket", "STORAGE_BUCKET"),
        ("storage_access_key", "STORAGE_ACCESS_KEY"),
        ("storage_secret_key", "STORAGE_SECRET_KEY"),
    ],
)
@pytest.mark.parametrize("value", [None, "", "   "])
def test_production_rejects_missing_storage_settings(
    field: str, variable: str, value: str | None
) -> None:
    with pytest.raises(SecurityConfigurationError, match=variable):
        validate_security_configuration(_production_settings(**{field: value}))


def test_production_does_not_require_external_storage_keys() -> None:
    settings = _production_settings(
        storage_external_access_key=None, storage_external_secret_key=None
    )

    validate_security_configuration(settings)


def test_storage_validation_errors_do_not_expose_secrets() -> None:
    secret = f"storage-secret-{uuid4()}"

    with pytest.raises(SecurityConfigurationError) as error:
        validate_security_configuration(
            _production_settings(storage_secret_key=secret, storage_access_key=None)
        )

    assert secret not in str(error.value)


@pytest.mark.parametrize(
    "endpoint_url",
    [None, "", "   ", "http://storage.yandexcloud.net", "https://", "storage.yandexcloud.net"],
)
def test_production_requires_https_storage_endpoint(endpoint_url: str | None) -> None:
    with pytest.raises(SecurityConfigurationError, match="STORAGE_ENDPOINT_URL"):
        validate_security_configuration(
            _production_settings(storage_endpoint_url=endpoint_url)
        )


@pytest.mark.parametrize(
    ("field", "variable"),
    [
        ("storage_access_key", "STORAGE_ACCESS_KEY"),
        ("storage_secret_key", "STORAGE_SECRET_KEY"),
    ],
)
def test_configured_bucket_requires_explicit_keys_outside_production(
    field: str, variable: str
) -> None:
    values: dict[str, object] = {
        "storage_bucket": "safetymain-documents",
        "storage_access_key": "access",
        "storage_secret_key": "secret",
    }
    values[field] = None

    with pytest.raises(SecurityConfigurationError, match=variable):
        validate_security_configuration(AppSettings(**values))


def test_development_without_bucket_needs_no_storage_keys() -> None:
    validate_security_configuration(AppSettings(storage_bucket=None))
