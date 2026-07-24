from __future__ import annotations

from backend.core.application.exceptions.authentication import (
    AuthenticationForbiddenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from backend.core.contracts.token_service import TokenValidationError
from backend.core.domain.exceptions.refresh_session import RefreshSessionError

INVALID_CREDENTIALS = "invalid_credentials"
AUTHENTICATION_FORBIDDEN = "authentication_forbidden"
INVALID_REFRESH_TOKEN = "invalid_refresh_token"
EXPIRED_REFRESH_TOKEN = "expired_refresh_token"
INVALID_TOKEN_TYPE = "invalid_token_type"
INVALID_TOKEN_CLAIMS = "invalid_token_claims"
SESSION_NOT_FOUND = "session_not_found"
SESSION_REVOKED = "session_revoked"
SESSION_EXPIRED = "session_expired"
SESSION_SUBJECT_MISMATCH = "session_subject_mismatch"
SESSION_FAMILY_MISMATCH = "session_family_mismatch"
REFRESH_TOKEN_REUSE_DETECTED = "refresh_token_reuse_detected"
REFRESH_ROTATION_CONFLICT = "refresh_rotation_conflict"

AUTHENTICATION_LOGIN_FAILURE_CODES: frozenset[str] = frozenset(
    {
        INVALID_CREDENTIALS,
        AUTHENTICATION_FORBIDDEN,
    }
)

AUTHENTICATION_REFRESH_FAILURE_CODES: frozenset[str] = frozenset(
    {
        INVALID_REFRESH_TOKEN,
        EXPIRED_REFRESH_TOKEN,
        INVALID_TOKEN_TYPE,
        INVALID_TOKEN_CLAIMS,
        AUTHENTICATION_FORBIDDEN,
        SESSION_NOT_FOUND,
        SESSION_REVOKED,
        SESSION_EXPIRED,
        SESSION_SUBJECT_MISMATCH,
        SESSION_FAMILY_MISMATCH,
        REFRESH_TOKEN_REUSE_DETECTED,
        REFRESH_ROTATION_CONFLICT,
    }
)

LOGIN_FAILURE_CODES_BY_EXCEPTION: dict[type[Exception], str] = {
    InvalidCredentialsError: INVALID_CREDENTIALS,
    AuthenticationForbiddenError: AUTHENTICATION_FORBIDDEN,
}

REFRESH_FAILURE_FALLBACK_CODE = INVALID_REFRESH_TOKEN


def refresh_failure_code_for_token_error(error: TokenValidationError) -> str:
    reason = getattr(error, "reason", None)
    if isinstance(reason, str) and reason in AUTHENTICATION_REFRESH_FAILURE_CODES:
        return reason
    return REFRESH_FAILURE_FALLBACK_CODE


def refresh_failure_code_for_exception(error: Exception) -> str:
    if isinstance(error, TokenValidationError):
        return refresh_failure_code_for_token_error(error)
    if isinstance(error, RefreshSessionError):
        reason = getattr(error, "reason", None)
        if isinstance(reason, str) and reason in AUTHENTICATION_REFRESH_FAILURE_CODES:
            return reason
        return REFRESH_FAILURE_FALLBACK_CODE
    if isinstance(error, InvalidRefreshTokenError):
        cause = error.__cause__
        if isinstance(cause, TokenValidationError):
            return refresh_failure_code_for_token_error(cause)
        if isinstance(cause, RefreshSessionError):
            return refresh_failure_code_for_exception(cause)
        return REFRESH_FAILURE_FALLBACK_CODE
    return REFRESH_FAILURE_FALLBACK_CODE
