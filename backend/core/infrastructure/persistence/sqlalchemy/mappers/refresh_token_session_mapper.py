from __future__ import annotations

from backend.core.domain.entities.refresh_token_session import RefreshTokenSession
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshSessionRevocationReason,
    RefreshTokenFamilyId,
    RefreshTokenIdHash,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.refresh_token_session_model import (
    RefreshTokenSessionModel,
)


def to_model(session: RefreshTokenSession) -> RefreshTokenSessionModel:
    return RefreshTokenSessionModel(
        session_id=session.session_id.value,
        user_id=session.user_id.value,
        family_id=session.family_id.value,
        current_token_id_hash=session.current_token_id_hash.value,
        previous_token_id_hash=(
            session.previous_token_id_hash.value if session.previous_token_id_hash else None
        ),
        created_at=session.created_at,
        last_rotated_at=session.last_rotated_at,
        expires_at=session.expires_at,
        absolute_expires_at=session.absolute_expires_at,
        revoked_at=session.revoked_at,
        revocation_reason=(
            session.revocation_reason.value if session.revocation_reason else None
        ),
    )


def apply_to_model(model: RefreshTokenSessionModel, session: RefreshTokenSession) -> None:
    model.current_token_id_hash = session.current_token_id_hash.value
    model.previous_token_id_hash = (
        session.previous_token_id_hash.value if session.previous_token_id_hash else None
    )
    model.last_rotated_at = session.last_rotated_at
    model.expires_at = session.expires_at
    model.revoked_at = session.revoked_at
    model.revocation_reason = (
        session.revocation_reason.value if session.revocation_reason else None
    )


def to_domain(model: RefreshTokenSessionModel) -> RefreshTokenSession:
    return RefreshTokenSession(
        session_id=RefreshSessionId(value=model.session_id),
        user_id=UserId(value=model.user_id),
        family_id=RefreshTokenFamilyId(value=model.family_id),
        current_token_id_hash=RefreshTokenIdHash(value=model.current_token_id_hash),
        previous_token_id_hash=(
            RefreshTokenIdHash(value=model.previous_token_id_hash)
            if model.previous_token_id_hash
            else None
        ),
        created_at=model.created_at,
        last_rotated_at=model.last_rotated_at,
        expires_at=model.expires_at,
        absolute_expires_at=model.absolute_expires_at,
        revoked_at=model.revoked_at,
        revocation_reason=(
            RefreshSessionRevocationReason(model.revocation_reason)
            if model.revocation_reason
            else None
        ),
    )
