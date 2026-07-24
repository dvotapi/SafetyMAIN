from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.core.contracts.token_service import AuthenticationTokens, RefreshTokenIssueSpec
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshTokenFamilyId,
)
from backend.core.infrastructure.auth.jwt_token_service import JwtTokenService


def issue_test_tokens(
    token_service: JwtTokenService,
    user_id: UserId,
    *,
    organization_id: OrganizationId | None = None,
    refresh_ttl_seconds: int | None = None,
) -> AuthenticationTokens:
    ttl = refresh_ttl_seconds or token_service._refresh_token_ttl_seconds
    return token_service.issue_tokens(
        user_id,
        organization_id=organization_id,
        refresh=RefreshTokenIssueSpec(
            session_id=RefreshSessionId(value=uuid4()),
            family_id=RefreshTokenFamilyId(value=uuid4()),
            jti=str(uuid4()),
            ttl_seconds=ttl,
        ),
    )
