from __future__ import annotations

import pytest

from backend.bootstrap.settings import AppSettings, load_settings


def test_load_settings_defaults() -> None:
    settings = load_settings(environment={})
    assert settings == AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="development",
        database_url=None,
        cors_allowed_origins=(),
        jwt_secret_key="dev-insecure-change-me",
        jwt_algorithm="HS256",
        jwt_access_token_ttl_seconds=3600,
        jwt_refresh_token_ttl_seconds=604800,
        jwt_issuer="safetymain",
        auth_enforcement=False,
        default_organization_id=None,
    )


def test_load_settings_from_environment() -> None:
    settings = load_settings(
        environment={
            "APP_NAME": "Custom API",
            "APP_VERSION": "9.9.9",
            "APP_ENV": "staging",
            "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/db",
            "CORS_ALLOWED_ORIGINS": "https://a.example, https://b.example",
        }
    )
    assert settings.app_name == "Custom API"
    assert settings.app_version == "9.9.9"
    assert settings.app_env == "staging"
    assert settings.database_url == (
        "postgresql+psycopg://user:pass@localhost:5432/db"
    )
    assert settings.cors_allowed_origins == (
        "https://a.example",
        "https://b.example",
    )


def test_settings_do_not_require_database_url() -> None:
    settings = load_settings(environment={"APP_ENV": "test"})
    assert settings.database_url is None


def test_load_settings_rejects_non_positive_jwt_ttl() -> None:
    with pytest.raises(ValueError):
        load_settings(environment={"JWT_ACCESS_TOKEN_TTL_SECONDS": "0"})


def test_load_settings_parses_auth_enforcement_and_default_organization() -> None:
    org_id = "11111111-1111-1111-1111-111111111111"
    settings = load_settings(
        environment={
            "AUTH_ENFORCEMENT": "true",
            "DEFAULT_ORGANIZATION_ID": org_id,
        }
    )
    assert settings.auth_enforcement is True
    assert settings.default_organization_id is not None
    assert str(settings.default_organization_id.value) == org_id


def test_load_settings_rejects_invalid_auth_enforcement_value() -> None:
    with pytest.raises(ValueError, match="AUTH_ENFORCEMENT"):
        load_settings(environment={"AUTH_ENFORCEMENT": "maybe"})


def test_load_settings_rejects_unsupported_jwt_algorithm() -> None:
    from backend.bootstrap.security_validation import SecurityConfigurationError

    with pytest.raises(SecurityConfigurationError, match="JWT_ALGORITHM"):
        load_settings(environment={"JWT_ALGORITHM": "RS256"})
