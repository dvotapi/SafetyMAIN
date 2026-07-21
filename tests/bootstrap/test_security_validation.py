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
