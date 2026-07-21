from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.core.domain.value_objects import OrganizationId, UserId


class TokenValidationError(Exception):
    """Raised when a token cannot be validated."""


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UserId
    organization_id: OrganizationId | None = None


@dataclass(frozen=True, slots=True)
class AuthenticationTokens:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenServiceContract(Protocol):
    """Contract for issuing and validating authentication tokens."""

    def issue_tokens(self, user_id: UserId) -> AuthenticationTokens:
        ...

    def refresh_tokens(self, refresh_token: str) -> AuthenticationTokens:
        ...

    def validate_access_token(self, token: str) -> UserId:
        ...

    def validate_access_token_claims(self, token: str) -> AccessTokenClaims:
        ...
