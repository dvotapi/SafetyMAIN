from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


APP_NAME_ENV = "APP_NAME"
APP_VERSION_ENV = "APP_VERSION"
APP_ENV_ENV = "APP_ENV"
DATABASE_URL_ENV = "DATABASE_URL"
CORS_ALLOWED_ORIGINS_ENV = "CORS_ALLOWED_ORIGINS"
JWT_SECRET_KEY_ENV = "JWT_SECRET_KEY"
JWT_ALGORITHM_ENV = "JWT_ALGORITHM"
JWT_ACCESS_TOKEN_TTL_SECONDS_ENV = "JWT_ACCESS_TOKEN_TTL_SECONDS"
JWT_REFRESH_TOKEN_TTL_SECONDS_ENV = "JWT_REFRESH_TOKEN_TTL_SECONDS"
JWT_ISSUER_ENV = "JWT_ISSUER"

DEFAULT_APP_NAME = "SafetyMAIN API"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_APP_ENV = "development"
DEFAULT_JWT_SECRET_KEY = "dev-insecure-change-me"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS = 3600
DEFAULT_JWT_REFRESH_TOKEN_TTL_SECONDS = 604_800
DEFAULT_JWT_ISSUER = "safetymain"


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
    jwt_secret_key: str = DEFAULT_JWT_SECRET_KEY
    jwt_algorithm: str = DEFAULT_JWT_ALGORITHM
    jwt_access_token_ttl_seconds: int = DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS
    jwt_refresh_token_ttl_seconds: int = DEFAULT_JWT_REFRESH_TOKEN_TTL_SECONDS
    jwt_issuer: str | None = DEFAULT_JWT_ISSUER


def _read_positive_int(raw_value: str, *, default: int) -> int:
    value = raw_value.strip()
    if not value:
        return default
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("JWT token TTL must be a positive integer.")
    return parsed


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

    jwt_issuer = source.get(JWT_ISSUER_ENV, DEFAULT_JWT_ISSUER)
    if jwt_issuer is not None:
        jwt_issuer = jwt_issuer.strip() or None

    return AppSettings(
        app_name=source.get(APP_NAME_ENV, DEFAULT_APP_NAME).strip() or DEFAULT_APP_NAME,
        app_version=(
            source.get(APP_VERSION_ENV, DEFAULT_APP_VERSION).strip() or DEFAULT_APP_VERSION
        ),
        app_env=source.get(APP_ENV_ENV, DEFAULT_APP_ENV).strip() or DEFAULT_APP_ENV,
        database_url=database_url,
        cors_allowed_origins=cors_origins,
        jwt_secret_key=(
            source.get(JWT_SECRET_KEY_ENV, DEFAULT_JWT_SECRET_KEY).strip()
            or DEFAULT_JWT_SECRET_KEY
        ),
        jwt_algorithm=(
            source.get(JWT_ALGORITHM_ENV, DEFAULT_JWT_ALGORITHM).strip()
            or DEFAULT_JWT_ALGORITHM
        ),
        jwt_access_token_ttl_seconds=_read_positive_int(
            source.get(
                JWT_ACCESS_TOKEN_TTL_SECONDS_ENV,
                str(DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS),
            ),
            default=DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS,
        ),
        jwt_refresh_token_ttl_seconds=_read_positive_int(
            source.get(
                JWT_REFRESH_TOKEN_TTL_SECONDS_ENV,
                str(DEFAULT_JWT_REFRESH_TOKEN_TTL_SECONDS),
            ),
            default=DEFAULT_JWT_REFRESH_TOKEN_TTL_SECONDS,
        ),
        jwt_issuer=jwt_issuer,
    )
