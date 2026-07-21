from __future__ import annotations

from backend.bootstrap.settings import (
    DEFAULT_JWT_SECRET_KEY,
    AppSettings,
)

SUPPORTED_JWT_ALGORITHMS: frozenset[str] = frozenset({"HS256", "HS384", "HS512"})

MIN_ACCESS_TOKEN_TTL_SECONDS = 60
MAX_ACCESS_TOKEN_TTL_SECONDS = 86_400
MIN_REFRESH_TOKEN_TTL_SECONDS = 300
MAX_REFRESH_TOKEN_TTL_SECONDS = 7_776_000

MIN_PRODUCTION_JWT_SECRET_LENGTH = 32

INSECURE_JWT_SECRET_VALUES: frozenset[str] = frozenset(
    {
        "secret",
        "changeme",
        "change-me",
        "development",
        "dev-secret",
        "test-secret",
        DEFAULT_JWT_SECRET_KEY.lower(),
    }
)


class SecurityConfigurationError(ValueError):
    """Raised when security-related settings are invalid or unsafe."""


def validate_security_configuration(settings: AppSettings) -> None:
    """Validate security settings before dependency construction."""

    _validate_jwt_algorithm(settings.jwt_algorithm)
    _validate_token_lifetimes(
        access_token_ttl_seconds=settings.jwt_access_token_ttl_seconds,
        refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
    )
    _validate_jwt_issuer(settings.jwt_issuer)
    _validate_auth_enforcement(settings.auth_enforcement)

    if _is_production_environment(settings.app_env):
        _validate_production_security_configuration(settings)


def _is_production_environment(app_env: str) -> bool:
    return app_env.strip().lower() == "production"


def _validate_jwt_algorithm(algorithm: str) -> None:
    normalized = algorithm.strip()
    if not normalized:
        raise SecurityConfigurationError("JWT_ALGORITHM must not be empty.")

    if normalized not in SUPPORTED_JWT_ALGORITHMS:
        supported = ", ".join(sorted(SUPPORTED_JWT_ALGORITHMS))
        raise SecurityConfigurationError(
            f"JWT_ALGORITHM must be one of: {supported}."
        )


def _validate_token_lifetimes(
    *,
    access_token_ttl_seconds: int,
    refresh_token_ttl_seconds: int,
) -> None:
    if access_token_ttl_seconds < MIN_ACCESS_TOKEN_TTL_SECONDS:
        raise SecurityConfigurationError(
            "JWT_ACCESS_TOKEN_TTL_SECONDS must be at least "
            f"{MIN_ACCESS_TOKEN_TTL_SECONDS} seconds."
        )
    if access_token_ttl_seconds > MAX_ACCESS_TOKEN_TTL_SECONDS:
        raise SecurityConfigurationError(
            "JWT_ACCESS_TOKEN_TTL_SECONDS must not exceed "
            f"{MAX_ACCESS_TOKEN_TTL_SECONDS} seconds."
        )
    if refresh_token_ttl_seconds < MIN_REFRESH_TOKEN_TTL_SECONDS:
        raise SecurityConfigurationError(
            "JWT_REFRESH_TOKEN_TTL_SECONDS must be at least "
            f"{MIN_REFRESH_TOKEN_TTL_SECONDS} seconds."
        )
    if refresh_token_ttl_seconds > MAX_REFRESH_TOKEN_TTL_SECONDS:
        raise SecurityConfigurationError(
            "JWT_REFRESH_TOKEN_TTL_SECONDS must not exceed "
            f"{MAX_REFRESH_TOKEN_TTL_SECONDS} seconds."
        )
    if refresh_token_ttl_seconds <= access_token_ttl_seconds:
        raise SecurityConfigurationError(
            "JWT_REFRESH_TOKEN_TTL_SECONDS must be greater than "
            "JWT_ACCESS_TOKEN_TTL_SECONDS."
        )


def _validate_jwt_issuer(jwt_issuer: str | None) -> None:
    if jwt_issuer is None:
        return

    normalized = jwt_issuer.strip()
    if not normalized:
        raise SecurityConfigurationError(
            "JWT_ISSUER must be omitted or a non-empty value after trimming."
        )
    if len(normalized) > 256:
        raise SecurityConfigurationError(
            "JWT_ISSUER must not exceed 256 characters."
        )


def _validate_auth_enforcement(auth_enforcement: bool) -> None:
    if not isinstance(auth_enforcement, bool):
        raise SecurityConfigurationError(
            "AUTH_ENFORCEMENT must resolve to a boolean value."
        )


def _validate_production_security_configuration(settings: AppSettings) -> None:
    _validate_production_jwt_secret(settings.jwt_secret_key)

    if settings.jwt_issuer is None:
        raise SecurityConfigurationError(
            "JWT_ISSUER must be configured in production."
        )

    if not settings.auth_enforcement:
        raise SecurityConfigurationError(
            "AUTH_ENFORCEMENT must be true in production."
        )

    if not settings.database_url:
        raise SecurityConfigurationError(
            "DATABASE_URL must be configured in production for persistent identity."
        )


def _validate_production_jwt_secret(jwt_secret_key: str) -> None:
    normalized = jwt_secret_key.strip()
    if not normalized:
        raise SecurityConfigurationError("JWT_SECRET_KEY must not be empty.")

    lowered = normalized.lower()
    if lowered in INSECURE_JWT_SECRET_VALUES:
        raise SecurityConfigurationError(
            "JWT_SECRET_KEY must not use a development placeholder in production."
        )

    if len(normalized) < MIN_PRODUCTION_JWT_SECRET_LENGTH:
        raise SecurityConfigurationError(
            "JWT_SECRET_KEY must be at least "
            f"{MIN_PRODUCTION_JWT_SECRET_LENGTH} characters in production."
        )
