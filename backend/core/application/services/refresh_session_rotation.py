from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from backend.core.application.services.refresh_session_factory import (
    next_refresh_expiry,
    remaining_refresh_ttl_seconds,
)
from backend.core.contracts.token_service import (
    AuthenticationTokens,
    RefreshTokenClaims,
    RefreshTokenIssueSpec,
    TokenServiceContract,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.refresh_token_session import RefreshTokenSession
from backend.core.domain.exceptions.refresh_session import (
    RefreshRotationConflict,
    RefreshSessionExpired,
    RefreshSessionFamilyMismatch,
    RefreshSessionNotFound,
    RefreshSessionRevoked,
    RefreshSessionSubjectMismatch,
    RefreshTokenReuseDetected,
)
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionRevocationReason,
    RefreshTokenIdHash,
)


def validate_refresh_session_against_claims(
    session: RefreshTokenSession | None,
    claims: RefreshTokenClaims,
    *,
    now: datetime,
) -> RefreshTokenSession:
    if session is None:
        raise RefreshSessionNotFound(claims.session_id)
    if session.user_id != claims.user_id:
        raise RefreshSessionSubjectMismatch(session.session_id)
    if session.family_id != claims.family_id:
        raise RefreshSessionFamilyMismatch(session.session_id)
    if session.is_revoked():
        raise RefreshSessionRevoked(session.session_id)
    if session.is_expired(now=now):
        raise RefreshSessionExpired(session.session_id)

    presented_hash = RefreshTokenIdHash(value=hash_refresh_token_jti(claims.jti))
    if presented_hash != session.current_token_id_hash:
        raise RefreshTokenReuseDetected(session.session_id)
    return session


def rotate_refresh_session(
    unit_of_work: UnitOfWorkContract,
    token_service: TokenServiceContract,
    *,
    session: RefreshTokenSession,
    claims: RefreshTokenClaims,
    now: datetime,
    sliding_ttl_seconds: int,
) -> AuthenticationTokens:
    """Issue the next token pair, then atomically rotate the persisted session."""

    presented_hash = RefreshTokenIdHash(value=hash_refresh_token_jti(claims.jti))
    new_jti = str(uuid4())
    expires_at = next_refresh_expiry(
        now=now,
        sliding_ttl_seconds=sliding_ttl_seconds,
        absolute_expires_at=session.absolute_expires_at,
    )
    ttl_seconds = remaining_refresh_ttl_seconds(now=now, expires_at=expires_at)
    tokens = token_service.issue_tokens(
        session.user_id,
        refresh=RefreshTokenIssueSpec(
            session_id=session.session_id,
            family_id=session.family_id,
            jti=new_jti,
            ttl_seconds=ttl_seconds,
        ),
    )
    rotated = unit_of_work.refresh_sessions.rotate(
        session.session_id,
        expected_token_id_hash=presented_hash,
        new_token_id_hash=RefreshTokenIdHash(value=hash_refresh_token_jti(new_jti)),
        rotated_at=now,
        expires_at=expires_at,
    )
    if not rotated:
        raise RefreshRotationConflict(session.session_id)
    return tokens


def revoke_session_for_reuse(
    unit_of_work: UnitOfWorkContract,
    *,
    session_id,
    now: datetime,
) -> None:
    unit_of_work.refresh_sessions.revoke(
        session_id,
        revoked_at=now,
        reason=RefreshSessionRevocationReason.TOKEN_REUSE_DETECTED,
    )
