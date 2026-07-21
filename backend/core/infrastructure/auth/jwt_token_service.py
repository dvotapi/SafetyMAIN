from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from backend.core.contracts.token_service import (
    AccessTokenClaims,
    AuthenticationTokens,
    TokenServiceContract,
    TokenValidationError,
)
from backend.core.domain.value_objects import OrganizationId, UserId


class JwtTokenService:
    """JWT-backed token service using symmetric signing."""

    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
        issuer: str | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._issuer = issuer

    def issue_tokens(
        self,
        user_id: UserId,
        *,
        organization_id: OrganizationId | None = None,
    ) -> AuthenticationTokens:
        return AuthenticationTokens(
            access_token=self._encode_token(
                user_id=user_id,
                token_type="access",
                ttl_seconds=self._access_token_ttl_seconds,
                organization_id=organization_id,
            ),
            refresh_token=self._encode_token(
                user_id=user_id,
                token_type="refresh",
                ttl_seconds=self._refresh_token_ttl_seconds,
            ),
            token_type="bearer",
            expires_in=self._access_token_ttl_seconds,
        )

    def refresh_tokens(self, refresh_token: str) -> AuthenticationTokens:
        user_id, _organization_id = self._decode_token(refresh_token, expected_type="refresh")
        return self.issue_tokens(user_id)

    def validate_access_token(self, token: str) -> UserId:
        return self.validate_access_token_claims(token).user_id

    def validate_access_token_claims(self, token: str) -> AccessTokenClaims:
        user_id, organization_id = self._decode_token(
            token,
            expected_type="access",
        )
        return AccessTokenClaims(user_id=user_id, organization_id=organization_id)

    def _encode_token(
        self,
        *,
        user_id: UserId,
        token_type: str,
        ttl_seconds: int,
        organization_id: OrganizationId | None = None,
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, object] = {
            "sub": str(user_id.value),
            "typ": token_type,
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        }
        if self._issuer is not None:
            payload["iss"] = self._issuer
        if organization_id is not None:
            payload["org_id"] = str(organization_id.value)

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def _decode_token(
        self,
        token: str,
        *,
        expected_type: str,
    ) -> tuple[UserId, OrganizationId | None]:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["exp", "sub", "typ"]},
            )
        except jwt.PyJWTError as exc:
            raise TokenValidationError("Token validation failed.") from exc

        token_type = payload.get("typ")
        if token_type != expected_type:
            raise TokenValidationError("Unexpected token type.")

        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise TokenValidationError("Token subject is missing.")

        try:
            return UserId(value=subject), self._parse_organization_claim(payload.get("org_id"))
        except Exception as exc:
            raise TokenValidationError("Token subject is invalid.") from exc

    def _parse_organization_claim(self, raw_value: object) -> OrganizationId | None:
        if raw_value is None:
            return None
        if not isinstance(raw_value, str):
            raise TokenValidationError("Token organization claim is invalid.")
        try:
            return OrganizationId(value=raw_value)
        except Exception as exc:
            raise TokenValidationError("Token organization claim is invalid.") from exc


def create_token_service(
    *,
    secret_key: str,
    algorithm: str,
    access_token_ttl_seconds: int,
    refresh_token_ttl_seconds: int,
    issuer: str | None = None,
) -> TokenServiceContract:
    return JwtTokenService(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_ttl_seconds=access_token_ttl_seconds,
        refresh_token_ttl_seconds=refresh_token_ttl_seconds,
        issuer=issuer,
    )
