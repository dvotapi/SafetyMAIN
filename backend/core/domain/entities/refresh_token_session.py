from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshSessionRevocationReason,
    RefreshTokenFamilyId,
    RefreshTokenIdHash,
)


class RefreshTokenSession(BaseModel):
    """Persistent refresh-token family/session state."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    session_id: RefreshSessionId = Field(frozen=True)
    user_id: UserId = Field(frozen=True)
    family_id: RefreshTokenFamilyId = Field(frozen=True)
    current_token_id_hash: RefreshTokenIdHash
    previous_token_id_hash: RefreshTokenIdHash | None = None
    created_at: datetime = Field(frozen=True)
    last_rotated_at: datetime
    expires_at: datetime
    absolute_expires_at: datetime = Field(frozen=True)
    revoked_at: datetime | None = None
    revocation_reason: RefreshSessionRevocationReason | None = None

    @model_validator(mode="after")
    def validate_expiration_window(self) -> RefreshTokenSession:
        if self.expires_at > self.absolute_expires_at:
            raise ValueError("Session expires_at cannot exceed absolute_expires_at.")
        if self.created_at > self.absolute_expires_at:
            raise ValueError("Session absolute_expires_at must be after created_at.")
        if self.revoked_at is None and self.revocation_reason is not None:
            raise ValueError("Revocation reason requires revoked_at.")
        if self.revoked_at is not None and self.revocation_reason is None:
            raise ValueError("revoked_at requires a revocation reason.")
        return self

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, *, now: datetime) -> bool:
        return now >= self.expires_at or now >= self.absolute_expires_at

    def is_active(self, *, now: datetime) -> bool:
        return not self.is_revoked() and not self.is_expired(now=now)
