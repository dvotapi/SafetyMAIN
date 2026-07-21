from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import jwt
import pytest

from backend.core.contracts.token_service import TokenValidationError
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.infrastructure.auth.jwt_token_service import JwtTokenService


@pytest.fixture
def token_service() -> JwtTokenService:
    return JwtTokenService(
        secret_key="test-secret-key-with-sufficient-length",
        algorithm="HS256",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=604800,
        issuer="safetymain",
    )


def test_jwt_token_service_issues_and_validates_access_token(
    token_service: JwtTokenService,
) -> None:
    user_id = UserId(value=uuid4())

    tokens = token_service.issue_tokens(user_id)

    assert token_service.validate_access_token(tokens.access_token) == user_id


def test_jwt_token_service_rejects_refresh_token_as_access_token(
    token_service: JwtTokenService,
) -> None:
    user_id = UserId(value=uuid4())
    tokens = token_service.issue_tokens(user_id)

    with pytest.raises(TokenValidationError):
        token_service.validate_access_token(tokens.refresh_token)


def test_jwt_token_service_refreshes_tokens(token_service: JwtTokenService) -> None:
    user_id = UserId(value=uuid4())
    tokens = token_service.issue_tokens(user_id)

    refreshed = token_service.refresh_tokens(tokens.refresh_token)

    assert token_service.validate_access_token(refreshed.access_token) == user_id


def test_jwt_token_service_exposes_optional_organization_claim(
    token_service: JwtTokenService,
) -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    tokens = token_service.issue_tokens(user_id, organization_id=organization_id)

    claims = token_service.validate_access_token_claims(tokens.access_token)

    assert claims.user_id == user_id
    assert claims.organization_id == organization_id


def test_jwt_token_service_rejects_invalid_issuer(token_service: JwtTokenService) -> None:
    user_id = UserId(value=uuid4())
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id.value),
        "typ": "access",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + 3600,
        "iss": "wrong-issuer",
    }
    token = jwt.encode(
        payload,
        "test-secret-key-with-sufficient-length",
        algorithm="HS256",
    )

    with pytest.raises(TokenValidationError):
        token_service.validate_access_token(token)
