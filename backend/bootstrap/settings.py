from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


APP_NAME_ENV = "APP_NAME"
APP_VERSION_ENV = "APP_VERSION"
APP_ENV_ENV = "APP_ENV"
DATABASE_URL_ENV = "DATABASE_URL"
CORS_ALLOWED_ORIGINS_ENV = "CORS_ALLOWED_ORIGINS"

DEFAULT_APP_NAME = "SafetyMAIN API"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_APP_ENV = "development"


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Typed application settings loaded from the environment.

    Construction does not open a database connection.
    """

    app_name: str = DEFAULT_APP_NAME
    app_version: str = DEFAULT_APP_VERSION
    app_env: str = DEFAULT_APP_ENV
    database_url: str | None = None
    cors_allowed_origins: tuple[str, ...] = ()


def load_settings(environment: Mapping[str, str] | None = None) -> AppSettings:
    source = environment if environment is not None else os.environ
    cors_raw = source.get(CORS_ALLOWED_ORIGINS_ENV, "").strip()
    cors_origins = tuple(
        origin.strip()
        for origin in cors_raw.split(",")
        if origin.strip()
    )

    database_url = source.get(DATABASE_URL_ENV)
    if database_url is not None:
        database_url = database_url.strip() or None

    return AppSettings(
        app_name=source.get(APP_NAME_ENV, DEFAULT_APP_NAME).strip() or DEFAULT_APP_NAME,
        app_version=(
            source.get(APP_VERSION_ENV, DEFAULT_APP_VERSION).strip() or DEFAULT_APP_VERSION
        ),
        app_env=source.get(APP_ENV_ENV, DEFAULT_APP_ENV).strip() or DEFAULT_APP_ENV,
        database_url=database_url,
        cors_allowed_origins=cors_origins,
    )
