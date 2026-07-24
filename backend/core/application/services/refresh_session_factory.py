from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from backend.core.domain.entities.refresh_token_session import RefreshTokenSession
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshTokenFamilyId,
    RefreshTokenIdHash,
)


def create_refresh_token_session(
    *,
    user_id: UserId,
    now: datetime,
    sliding_ttl_seconds: int,
    absolute_ttl_seconds: int,
    jti: str | None = None,
) -> tuple[RefreshTokenSession, str]:
    """Create a new refresh session and its initial raw jti.

    The raw jti is returned for JWT issuance and must not be persisted.
    """

    raw_jti = jti or str(uuid4())
    absolute_expires_at = now + timedelta(seconds=absolute_ttl_seconds)
    expires_at = min(now + timedelta(seconds=sliding_ttl_seconds), absolute_expires_at)
    session = RefreshTokenSession(
        session_id=RefreshSessionId(value=uuid4()),
        user_id=user_id,
        family_id=RefreshTokenFamilyId(value=uuid4()),
        current_token_id_hash=RefreshTokenIdHash(value=hash_refresh_token_jti(raw_jti)),
        previous_token_id_hash=None,
        created_at=now,
        last_rotated_at=now,
        expires_at=expires_at,
        absolute_expires_at=absolute_expires_at,
        revoked_at=None,
        revocation_reason=None,
    )
    return session, raw_jti


def next_refresh_expiry(
    *,
    now: datetime,
    sliding_ttl_seconds: int,
    absolute_expires_at: datetime,
) -> datetime:
    return min(now + timedelta(seconds=sliding_ttl_seconds), absolute_expires_at)


def remaining_refresh_ttl_seconds(
    *,
    now: datetime,
    expires_at: datetime,
) -> int:
    remaining = int((expires_at - now).total_seconds())
    if remaining <= 0:
        raise ValueError("Refresh TTL must remain positive.")
    return remaining
