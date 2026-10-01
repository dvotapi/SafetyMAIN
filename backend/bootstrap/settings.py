from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from backend.core.domain.value_objects import OrganizationId


APP_NAME_ENV = "APP_NAME"
APP_VERSION_ENV = "APP_VERSION"
APP_ENV_ENV = "APP_ENV"
DATABASE_URL_ENV = "DATABASE_URL"
CORS_ALLOWED_ORIGINS_ENV = "CORS_ALLOWED_ORIGINS"
JWT_SECRET_KEY_ENV = "JWT_SECRET_KEY"
JWT_ALGORITHM_ENV = "JWT_ALGORITHM"
JWT_ACCESS_TOKEN_TTL_SECONDS_ENV = "JWT_ACCESS_TOKEN_TTL_SECONDS"
JWT_REFRESH_TOKEN_TTL_SECONDS_ENV = "JWT_REFRESH_TOKEN_TTL_SECONDS"
JWT_REFRESH_ABSOLUTE_TTL_SECONDS_ENV = "JWT_REFRESH_ABSOLUTE_TTL_SECONDS"
REFRESH_TOKEN_ROTATION_ENABLED_ENV = "REFRESH_TOKEN_ROTATION_ENABLED"
JWT_ISSUER_ENV = "JWT_ISSUER"
AUTH_ENFORCEMENT_ENV = "AUTH_ENFORCEMENT"
DEFAULT_ORGANIZATION_ID_ENV = "DEFAULT_ORGANIZATION_ID"
STORAGE_ENDPOINT_URL_ENV = "STORAGE_ENDPOINT_URL"
STORAGE_REGION_ENV = "STORAGE_REGION"
STORAGE_BUCKET_ENV = "STORAGE_BUCKET"
STORAGE_ACCESS_KEY_ENV = "STORAGE_ACCESS_KEY"
STORAGE_SECRET_KEY_ENV = "STORAGE_SECRET_KEY"
STORAGE_PRESIGN_TTL_SECONDS_ENV = "STORAGE_PRESIGN_TTL_SECONDS"
STORAGE_MAX_UPLOAD_BYTES_ENV = "STORAGE_MAX_UPLOAD_BYTES"
STORAGE_EXTERNAL_ACCESS_KEY_ENV = "STORAGE_EXTERNAL_ACCESS_KEY"
STORAGE_EXTERNAL_SECRET_KEY_ENV = "STORAGE_EXTERNAL_SECRET_KEY"

DEFAULT_APP_NAME = "SafetyMAIN API"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_APP_ENV = "development"
DEFAULT_JWT_SECRET_KEY = "dev-insecure-change-me"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS = 3600
DEFAULT_JWT_REFRESH_TOKEN_TTL_SECONDS = 604_800
DEFAULT_JWT_REFRESH_ABSOLUTE_TTL_SECONDS = 7_776_000
DEFAULT_REFRESH_TOKEN_ROTATION_ENABLED = True
DEFAULT_JWT_ISSUER = "safetymain"
DEFAULT_STORAGE_REGION = "us-east-1"
DEFAULT_STORAGE_PRESIGN_TTL_SECONDS = 900
DEFAULT_STORAGE_MAX_UPLOAD_BYTES = 50 * 1024 * 1024


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
    jwt_refresh_absolute_ttl_seconds: int = DEFAULT_JWT_REFRESH_ABSOLUTE_TTL_SECONDS
    refresh_token_rotation_enabled: bool = DEFAULT_REFRESH_TOKEN_ROTATION_ENABLED
    jwt_issuer: str | None = DEFAULT_JWT_ISSUER
    auth_enforcement: bool = False
    default_organization_id: OrganizationId | None = None
    storage_endpoint_url: str | None = None
    storage_region: str = DEFAULT_STORAGE_REGION
    storage_bucket: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_presign_ttl_seconds: int = DEFAULT_STORAGE_PRESIGN_TTL_SECONDS
    storage_max_upload_bytes: int = DEFAULT_STORAGE_MAX_UPLOAD_BYTES
    storage_external_access_key: str | None = None
    storage_external_secret_key: str | None = None


def _read_bool(raw_value: str, *, default: bool) -> bool:
    normalized = raw_value.strip().lower()
    if not normalized:
        return default
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("AUTH_ENFORCEMENT must be a boolean value.")


def _read_optional_organization_id(raw_value: str | None) -> OrganizationId | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    if not normalized:
        return None
    return OrganizationId(value=UUID(normalized))


def _read_positive_int(
    raw_value: str,
    *,
    default: int,
    error_message: str = "JWT token TTL must be a positive integer.",
) -> int:
    value = raw_value.strip()
    if not value:
        return default
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(error_message)
    return parsed


def _read_optional_str(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    return raw_value.strip() or None


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

    settings = AppSettings(
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
        jwt_refresh_absolute_ttl_seconds=_read_positive_int(
            source.get(
                JWT_REFRESH_ABSOLUTE_TTL_SECONDS_ENV,
                str(DEFAULT_JWT_REFRESH_ABSOLUTE_TTL_SECONDS),
            ),
            default=DEFAULT_JWT_REFRESH_ABSOLUTE_TTL_SECONDS,
        ),
        refresh_token_rotation_enabled=_read_bool(
            source.get(
                REFRESH_TOKEN_ROTATION_ENABLED_ENV,
                "true" if DEFAULT_REFRESH_TOKEN_ROTATION_ENABLED else "false",
            ),
            default=DEFAULT_REFRESH_TOKEN_ROTATION_ENABLED,
        ),
        jwt_issuer=jwt_issuer,
        auth_enforcement=_read_bool(
            source.get(AUTH_ENFORCEMENT_ENV, "false"),
            default=False,
        ),
        default_organization_id=_read_optional_organization_id(
            source.get(DEFAULT_ORGANIZATION_ID_ENV)
        ),
        storage_endpoint_url=_read_optional_str(source.get(STORAGE_ENDPOINT_URL_ENV)),
        storage_region=(
            source.get(STORAGE_REGION_ENV, DEFAULT_STORAGE_REGION).strip()
            or DEFAULT_STORAGE_REGION
        ),
        storage_bucket=_read_optional_str(source.get(STORAGE_BUCKET_ENV)),
        storage_access_key=_read_optional_str(source.get(STORAGE_ACCESS_KEY_ENV)),
        storage_secret_key=_read_optional_str(source.get(STORAGE_SECRET_KEY_ENV)),
        storage_presign_ttl_seconds=_read_positive_int(
            source.get(STORAGE_PRESIGN_TTL_SECONDS_ENV, ""),
            default=DEFAULT_STORAGE_PRESIGN_TTL_SECONDS,
            error_message="STORAGE_PRESIGN_TTL_SECONDS must be a positive integer.",
        ),
        storage_max_upload_bytes=_read_positive_int(
            source.get(STORAGE_MAX_UPLOAD_BYTES_ENV, ""),
            default=DEFAULT_STORAGE_MAX_UPLOAD_BYTES,
            error_message="STORAGE_MAX_UPLOAD_BYTES must be a positive integer.",
        ),
        storage_external_access_key=_read_optional_str(
            source.get(STORAGE_EXTERNAL_ACCESS_KEY_ENV)
        ),
        storage_external_secret_key=_read_optional_str(
            source.get(STORAGE_EXTERNAL_SECRET_KEY_ENV)
        ),
    )

    from backend.bootstrap.security_validation import validate_security_configuration

    validate_security_configuration(settings)
    return settings
