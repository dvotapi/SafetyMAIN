from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.core.domain.entities.refresh_token_session import RefreshTokenSession
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshSessionRevocationReason,
    RefreshTokenIdHash,
)


class RefreshTokenSessionRepositoryContract(Protocol):
    """Repository contract for persistent refresh-token sessions."""

    def add(self, session: RefreshTokenSession) -> None:
        ...

    def get_by_id(self, session_id: RefreshSessionId) -> RefreshTokenSession | None:
        ...

    def get_for_update(self, session_id: RefreshSessionId) -> RefreshTokenSession | None:
        ...

    def save(self, session: RefreshTokenSession) -> None:
        ...

    def rotate(
        self,
        session_id: RefreshSessionId,
        *,
        expected_token_id_hash: RefreshTokenIdHash,
        new_token_id_hash: RefreshTokenIdHash,
        rotated_at: datetime,
        expires_at: datetime,
    ) -> bool:
        """Atomically rotate when the expected current hash matches.

        Returns ``True`` when the row was updated.
        """

        ...

    def revoke(
        self,
        session_id: RefreshSessionId,
        *,
        revoked_at: datetime,
        reason: RefreshSessionRevocationReason,
    ) -> bool:
        """Revoke a session if it is not already revoked. Returns whether changed."""

        ...

    def revoke_all_for_user(
        self,
        user_id: UserId,
        *,
        revoked_at: datetime,
        reason: RefreshSessionRevocationReason,
    ) -> int:
        ...

    def delete_expired_before(self, cutoff: datetime) -> int:
        """Delete sessions whose retention window ended before ``cutoff``."""

        ...
