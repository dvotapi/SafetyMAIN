from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from backend.core.contracts.clock import ClockContract
from backend.core.contracts.token_service import (
    AccessTokenClaims,
    AuthenticationTokens,
    RefreshTokenClaims,
    RefreshTokenIssueSpec,
    TokenServiceContract,
    TokenValidationError,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshTokenFamilyId,
)
from backend.core.infrastructure.time.utc_clock import UtcClock


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
        clock: ClockContract | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._issuer = issuer
        self._clock = clock or UtcClock()

    def issue_tokens(
        self,
        user_id: UserId,
        *,
        refresh: RefreshTokenIssueSpec,
        organization_id: OrganizationId | None = None,
    ) -> AuthenticationTokens:
        if refresh.ttl_seconds <= 0:
            raise ValueError("Refresh token TTL must be positive.")
        return AuthenticationTokens(
            access_token=self.issue_access_token(
                user_id,
                organization_id=organization_id,
            ),
            refresh_token=self._encode_refresh_token(
                user_id=user_id,
                refresh=refresh,
            ),
            token_type="bearer",
            expires_in=self._access_token_ttl_seconds,
        )

    def issue_access_token(
        self,
        user_id: UserId,
        *,
        organization_id: OrganizationId | None = None,
    ) -> str:
        return self._encode_token(
            user_id=user_id,
            token_type="access",
            ttl_seconds=self._access_token_ttl_seconds,
            organization_id=organization_id,
        )

    def decode_refresh_token(self, refresh_token: str) -> RefreshTokenClaims:
        payload = self._decode_payload(refresh_token, expected_type="refresh")
        user_id = self._parse_user_id(payload.get("sub"))
        jti = payload.get("jti")
        session_raw = payload.get("session_id")
        family_raw = payload.get("family_id")
        exp = payload.get("exp")
        if not isinstance(jti, str) or not jti.strip():
            raise TokenValidationError(
                "Refresh token jti is missing.",
                reason="invalid_token_claims",
            )
        if not isinstance(session_raw, str) or not isinstance(family_raw, str):
            raise TokenValidationError(
                "Refresh session claims are missing.",
                reason="invalid_token_claims",
            )
        if not isinstance(exp, int):
            raise TokenValidationError(
                "Refresh token expiration is missing.",
                reason="invalid_token_claims",
            )
        try:
            return RefreshTokenClaims(
                user_id=user_id,
                jti=jti.strip(),
                session_id=RefreshSessionId(value=UUID(session_raw)),
                family_id=RefreshTokenFamilyId(value=UUID(family_raw)),
                expires_at=datetime.fromtimestamp(exp, tz=UTC),
            )
        except (TypeError, ValueError) as exc:
            raise TokenValidationError(
                "Refresh session claims are invalid.",
                reason="invalid_token_claims",
            ) from exc

    def validate_access_token(self, token: str) -> UserId:
        return self.validate_access_token_claims(token).user_id

    def validate_access_token_claims(self, token: str) -> AccessTokenClaims:
        payload = self._decode_payload(token, expected_type="access")
        return AccessTokenClaims(
            user_id=self._parse_user_id(payload.get("sub")),
            organization_id=self._parse_organization_claim(payload.get("org_id")),
        )

    def _encode_refresh_token(
        self,
        *,
        user_id: UserId,
        refresh: RefreshTokenIssueSpec,
    ) -> str:
        now = self._clock.now()
        payload: dict[str, object] = {
            "sub": str(user_id.value),
            "typ": "refresh",
            "jti": refresh.jti,
            "session_id": str(refresh.session_id.value),
            "family_id": str(refresh.family_id.value),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=refresh.ttl_seconds)).timestamp()),
        }
        if self._issuer is not None:
            payload["iss"] = self._issuer
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def _encode_token(
        self,
        *,
        user_id: UserId,
        token_type: str,
        ttl_seconds: int,
        organization_id: OrganizationId | None = None,
    ) -> str:
        now = self._clock.now()
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

    def _decode_payload(self, token: str, *, expected_type: str) -> dict[str, object]:
        decode_options: dict[str, object] = {"require": ["exp", "sub", "typ"]}
        decode_kwargs: dict[str, object] = {
            "algorithms": [self._algorithm],
            "options": decode_options,
        }
        if self._issuer is not None:
            decode_kwargs["issuer"] = self._issuer

        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                **decode_kwargs,
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenValidationError(
                "Token has expired.",
                reason="expired_refresh_token",
            ) from exc
        except jwt.InvalidIssuerError as exc:
            raise TokenValidationError(
                "Token issuer is invalid.",
                reason="invalid_token_claims",
            ) from exc
        except jwt.PyJWTError as exc:
            raise TokenValidationError(
                "Token validation failed.",
                reason="invalid_refresh_token",
            ) from exc

        token_type = payload.get("typ")
        if token_type != expected_type:
            raise TokenValidationError(
                "Unexpected token type.",
                reason="invalid_token_type",
            )
        if not isinstance(payload, dict):
            raise TokenValidationError(
                "Token payload is invalid.",
                reason="invalid_token_claims",
            )
        return payload

    def _parse_user_id(self, subject: object) -> UserId:
        if not isinstance(subject, str):
            raise TokenValidationError(
                "Token subject is missing.",
                reason="invalid_token_claims",
            )
        try:
            return UserId(value=subject)
        except Exception as exc:
            raise TokenValidationError(
                "Token subject is invalid.",
                reason="invalid_token_claims",
            ) from exc

    def _parse_organization_claim(self, raw_value: object) -> OrganizationId | None:
        if raw_value is None:
            return None
        if not isinstance(raw_value, str):
            raise TokenValidationError(
                "Token organization claim is invalid.",
                reason="invalid_token_claims",
            )
        try:
            return OrganizationId(value=raw_value)
        except Exception as exc:
            raise TokenValidationError(
                "Token organization claim is invalid.",
                reason="invalid_token_claims",
            ) from exc


def create_token_service(
    *,
    secret_key: str,
    algorithm: str,
    access_token_ttl_seconds: int,
    refresh_token_ttl_seconds: int,
    issuer: str | None = None,
    clock: ClockContract | None = None,
) -> TokenServiceContract:
    return JwtTokenService(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_ttl_seconds=access_token_ttl_seconds,
        refresh_token_ttl_seconds=refresh_token_ttl_seconds,
        issuer=issuer,
        clock=clock,
    )
