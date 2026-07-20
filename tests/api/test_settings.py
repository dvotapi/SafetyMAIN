from __future__ import annotations

from backend.bootstrap.settings import AppSettings, load_settings


def test_load_settings_defaults() -> None:
    settings = load_settings(environment={})
    assert settings == AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="development",
        database_url=None,
        cors_allowed_origins=(),
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
