from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from backend.core.contracts.user_credentials import UserCredentialsPort
from backend.core.contracts.user_lookup import UserLookupPort
from backend.core.domain.entities.user import User
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.user_mapper import to_model
from backend.core.infrastructure.persistence.sqlalchemy.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.session_scope import read_in_session


class SQLAlchemyIdentityAdapter(UserLookupPort, UserCredentialsPort):
    """SQLAlchemy-backed identity lookup for authentication."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register_user(self, user: User, password_hash: str) -> None:
        def _register(session: Session) -> None:
            session.add(to_model(user, password_hash=password_hash))

        from backend.core.infrastructure.persistence.sqlalchemy.session_scope import (
            run_in_session,
        )

        run_in_session(self._session_factory, _register)

    def get_user(self, user_id: UserId) -> User:
        def _get_user(session: Session) -> User:
            return SQLAlchemyUserRepository(session).get(user_id)

        return read_in_session(self._session_factory, _get_user)

    def get_user_by_email(self, email: str) -> User | None:
        def _get_user(session: Session) -> User | None:
            return SQLAlchemyUserRepository(session).get_by_email(email)

        return read_in_session(self._session_factory, _get_user)

    def get_user_by_external_subject(self, external_subject: str) -> User | None:
        def _get_user(session: Session) -> User | None:
            from sqlalchemy import select

            from backend.core.infrastructure.persistence.sqlalchemy.mappers.user_mapper import (
                to_domain,
            )
            from backend.core.infrastructure.persistence.sqlalchemy.models.user_model import (
                UserModel,
            )

            statement = select(UserModel).where(
                UserModel.external_subject == external_subject
            )
            model = session.scalar(statement)
            if model is None:
                return None
            return to_domain(model)

        return read_in_session(self._session_factory, _get_user)

    def get_password_hash(self, user_id: UserId) -> str | None:
        def _get_hash(session: Session) -> str | None:
            return SQLAlchemyUserRepository(session).get_password_hash(user_id)

        return read_in_session(self._session_factory, _get_hash)
