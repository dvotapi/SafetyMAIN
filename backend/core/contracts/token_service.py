from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshTokenFamilyId,
)


class TokenValidationError(Exception):
    """Raised when a token cannot be validated."""

    def __init__(
        self,
        message: str = "Token validation failed.",
        *,
        reason: str = "invalid_refresh_token",
    ) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UserId
    organization_id: OrganizationId | None = None


@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    user_id: UserId
    jti: str
    session_id: RefreshSessionId
    family_id: RefreshTokenFamilyId
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuthenticationTokens:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class RefreshTokenIssueSpec:
    session_id: RefreshSessionId
    family_id: RefreshTokenFamilyId
    jti: str
    ttl_seconds: int


class TokenServiceContract(Protocol):
    """Contract for issuing and validating authentication tokens."""

    def issue_tokens(
        self,
        user_id: UserId,
        *,
        refresh: RefreshTokenIssueSpec,
        organization_id: OrganizationId | None = None,
    ) -> AuthenticationTokens:
        ...

    def issue_access_token(
        self,
        user_id: UserId,
        *,
        organization_id: OrganizationId | None = None,
    ) -> str:
        ...

    def decode_refresh_token(self, refresh_token: str) -> RefreshTokenClaims:
        ...

    def validate_access_token(self, token: str) -> UserId:
        ...

    def validate_access_token_claims(self, token: str) -> AccessTokenClaims:
        ...
