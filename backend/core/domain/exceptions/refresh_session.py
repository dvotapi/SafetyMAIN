from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.refresh_session import RefreshSessionId


class RefreshSessionError(SafetyMainDomainError):
    """Base class for refresh-session domain errors."""

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class RefreshSessionNotFound(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId | None = None) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh session was not found.",
            reason="session_not_found",
        )


class RefreshSessionRevoked(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh session is revoked.",
            reason="session_revoked",
        )


class RefreshSessionExpired(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh session is expired.",
            reason="session_expired",
        )


class RefreshSessionSubjectMismatch(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh session subject does not match token subject.",
            reason="session_subject_mismatch",
        )


class RefreshSessionFamilyMismatch(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh session family does not match token family.",
            reason="session_family_mismatch",
        )


class RefreshTokenReuseDetected(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh token reuse was detected.",
            reason="refresh_token_reuse_detected",
        )


class RefreshRotationConflict(RefreshSessionError):
    def __init__(self, session_id: RefreshSessionId) -> None:
        self.session_id = session_id
        super().__init__(
            "Refresh token rotation conflict.",
            reason="refresh_rotation_conflict",
        )


class DuplicateRefreshTokenFamily(RefreshSessionError):
    def __init__(self) -> None:
        super().__init__(
            "Refresh token family already exists.",
            reason="duplicate_refresh_token_family",
        )
