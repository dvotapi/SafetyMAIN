from __future__ import annotations

from datetime import datetime
from threading import Lock

from backend.core.domain.entities.refresh_token_session import RefreshTokenSession
from backend.core.domain.exceptions.refresh_session import (
    DuplicateRefreshTokenFamily,
    RefreshSessionNotFound,
)
from backend.core.domain.repositories.refresh_token_session_repository import (
    RefreshTokenSessionRepositoryContract,
)
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionId,
    RefreshSessionRevocationReason,
    RefreshTokenFamilyId,
    RefreshTokenIdHash,
)


class InMemoryRefreshTokenSessionRepository(RefreshTokenSessionRepositoryContract):
    def __init__(self) -> None:
        self._sessions_by_id: dict[RefreshSessionId, RefreshTokenSession] = {}
        self._family_index: dict[RefreshTokenFamilyId, RefreshSessionId] = {}
        self._lock = Lock()

    def add(self, session: RefreshTokenSession) -> None:
        with self._lock:
            if session.family_id in self._family_index:
                raise DuplicateRefreshTokenFamily()
            if session.session_id in self._sessions_by_id:
                raise DuplicateRefreshTokenFamily()
            self._sessions_by_id[session.session_id] = session
            self._family_index[session.family_id] = session.session_id

    def get_by_id(self, session_id: RefreshSessionId) -> RefreshTokenSession | None:
        with self._lock:
            return self._sessions_by_id.get(session_id)

    def get_for_update(self, session_id: RefreshSessionId) -> RefreshTokenSession | None:
        return self.get_by_id(session_id)

    def save(self, session: RefreshTokenSession) -> None:
        with self._lock:
            if session.session_id not in self._sessions_by_id:
                raise RefreshSessionNotFound(session.session_id)
            self._sessions_by_id[session.session_id] = session

    def rotate(
        self,
        session_id: RefreshSessionId,
        *,
        expected_token_id_hash: RefreshTokenIdHash,
        new_token_id_hash: RefreshTokenIdHash,
        rotated_at: datetime,
        expires_at: datetime,
    ) -> bool:
        with self._lock:
            current = self._sessions_by_id.get(session_id)
            if current is None:
                return False
            if current.is_revoked():
                return False
            if current.current_token_id_hash != expected_token_id_hash:
                return False
            self._sessions_by_id[session_id] = current.model_copy(
                update={
                    "previous_token_id_hash": current.current_token_id_hash,
                    "current_token_id_hash": new_token_id_hash,
                    "last_rotated_at": rotated_at,
                    "expires_at": expires_at,
                }
            )
            return True

    def revoke(
        self,
        session_id: RefreshSessionId,
        *,
        revoked_at: datetime,
        reason: RefreshSessionRevocationReason,
    ) -> bool:
        with self._lock:
            current = self._sessions_by_id.get(session_id)
            if current is None or current.is_revoked():
                return False
            self._sessions_by_id[session_id] = current.model_copy(
                update={
                    "revoked_at": revoked_at,
                    "revocation_reason": reason,
                }
            )
            return True

    def revoke_all_for_user(
        self,
        user_id: UserId,
        *,
        revoked_at: datetime,
        reason: RefreshSessionRevocationReason,
    ) -> int:
        with self._lock:
            changed = 0
            for session_id, session in list(self._sessions_by_id.items()):
                if session.user_id != user_id or session.is_revoked():
                    continue
                self._sessions_by_id[session_id] = session.model_copy(
                    update={
                        "revoked_at": revoked_at,
                        "revocation_reason": reason,
                    }
                )
                changed += 1
            return changed

    def delete_expired_before(self, cutoff: datetime) -> int:
        with self._lock:
            removable = [
                session_id
                for session_id, session in self._sessions_by_id.items()
                if _retention_ended(session, cutoff=cutoff)
            ]
            for session_id in removable:
                session = self._sessions_by_id.pop(session_id)
                self._family_index.pop(session.family_id, None)
            return len(removable)

    def snapshot(
        self,
    ) -> tuple[
        dict[RefreshSessionId, RefreshTokenSession],
        dict[RefreshTokenFamilyId, RefreshSessionId],
    ]:
        with self._lock:
            return (dict(self._sessions_by_id), dict(self._family_index))

    def restore(
        self,
        snapshot: tuple[
            dict[RefreshSessionId, RefreshTokenSession],
            dict[RefreshTokenFamilyId, RefreshSessionId],
        ],
    ) -> None:
        sessions_by_id, family_index = snapshot
        with self._lock:
            self._sessions_by_id = dict(sessions_by_id)
            self._family_index = dict(family_index)


def _retention_ended(session: RefreshTokenSession, *, cutoff: datetime) -> bool:
    if session.revoked_at is not None:
        return session.revoked_at < cutoff
    return session.expires_at < cutoff and session.absolute_expires_at < cutoff
