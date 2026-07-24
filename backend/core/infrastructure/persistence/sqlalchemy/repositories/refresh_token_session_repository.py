from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
    RefreshTokenIdHash,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.refresh_token_session_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.refresh_token_session_model import (
    RefreshTokenSessionModel,
)


class SQLAlchemyRefreshTokenSessionRepository(RefreshTokenSessionRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, session: RefreshTokenSession) -> None:
        self._session.add(to_model(session))
        try:
            self._session.flush()
        except IntegrityError as error:
            message = str(getattr(error, "orig", error)).lower()
            if "uq_refresh_token_sessions_family_id" in message:
                raise DuplicateRefreshTokenFamily() from error
            raise

    def get_by_id(self, session_id: RefreshSessionId) -> RefreshTokenSession | None:
        model = self._session.get(RefreshTokenSessionModel, session_id.value)
        if model is None:
            return None
        return to_domain(model)

    def get_for_update(self, session_id: RefreshSessionId) -> RefreshTokenSession | None:
        statement = (
            select(RefreshTokenSessionModel)
            .where(RefreshTokenSessionModel.session_id == session_id.value)
            .with_for_update()
        )
        model = self._session.scalar(statement)
        if model is None:
            return None
        return to_domain(model)

    def save(self, session: RefreshTokenSession) -> None:
        model = self._session.get(RefreshTokenSessionModel, session.session_id.value)
        if model is None:
            raise RefreshSessionNotFound(session.session_id)
        apply_to_model(model, session)
        self._session.flush()

    def rotate(
        self,
        session_id: RefreshSessionId,
        *,
        expected_token_id_hash: RefreshTokenIdHash,
        new_token_id_hash: RefreshTokenIdHash,
        rotated_at: datetime,
        expires_at: datetime,
    ) -> bool:
        statement = (
            update(RefreshTokenSessionModel)
            .where(
                RefreshTokenSessionModel.session_id == session_id.value,
                RefreshTokenSessionModel.current_token_id_hash
                == expected_token_id_hash.value,
                RefreshTokenSessionModel.revoked_at.is_(None),
            )
            .values(
                previous_token_id_hash=expected_token_id_hash.value,
                current_token_id_hash=new_token_id_hash.value,
                last_rotated_at=rotated_at,
                expires_at=expires_at,
            )
        )
        result = self._session.execute(statement)
        self._session.flush()
        return bool(result.rowcount)

    def revoke(
        self,
        session_id: RefreshSessionId,
        *,
        revoked_at: datetime,
        reason: RefreshSessionRevocationReason,
    ) -> bool:
        statement = (
            update(RefreshTokenSessionModel)
            .where(
                RefreshTokenSessionModel.session_id == session_id.value,
                RefreshTokenSessionModel.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at,
                revocation_reason=reason.value,
            )
        )
        result = self._session.execute(statement)
        self._session.flush()
        return bool(result.rowcount)

    def revoke_all_for_user(
        self,
        user_id: UserId,
        *,
        revoked_at: datetime,
        reason: RefreshSessionRevocationReason,
    ) -> int:
        statement = (
            update(RefreshTokenSessionModel)
            .where(
                RefreshTokenSessionModel.user_id == user_id.value,
                RefreshTokenSessionModel.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at,
                revocation_reason=reason.value,
            )
        )
        result = self._session.execute(statement)
        self._session.flush()
        return int(result.rowcount or 0)

    def delete_expired_before(self, cutoff: datetime) -> int:
        statement = select(RefreshTokenSessionModel).where(
            or_(
                and_(
                    RefreshTokenSessionModel.revoked_at.is_not(None),
                    RefreshTokenSessionModel.revoked_at < cutoff,
                ),
                and_(
                    RefreshTokenSessionModel.revoked_at.is_(None),
                    RefreshTokenSessionModel.expires_at < cutoff,
                    RefreshTokenSessionModel.absolute_expires_at < cutoff,
                ),
            )
        )
        models = list(self._session.scalars(statement).all())
        for model in models:
            self._session.delete(model)
        self._session.flush()
        return len(models)
