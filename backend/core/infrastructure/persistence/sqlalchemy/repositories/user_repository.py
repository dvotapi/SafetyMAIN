from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.domain.entities.user import User
from backend.core.domain.exceptions import UserNotFound
from backend.core.domain.repositories import UserRepositoryContract
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.user_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(to_model(user, password_hash=""))

    def get(self, user_id: UserId) -> User:
        model = self._session.get(UserModel, user_id.value)
        if model is None:
            raise UserNotFound(user_id)
        return to_domain(model)

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        statement = select(UserModel).where(UserModel.email == normalized_email)
        model = self._session.scalar(statement)
        if model is None:
            return None
        return to_domain(model)

    def save(self, user: User) -> None:
        model = self._session.get(UserModel, user.id.value)
        if model is None:
            raise UserNotFound(user.id)
        apply_to_model(model, user)

    def get_password_hash(self, user_id: UserId) -> str | None:
        model = self._session.get(UserModel, user_id.value)
        if model is None:
            return None
        return model.password_hash

    def set_password_hash(self, user_id: UserId, password_hash: str) -> None:
        model = self._session.get(UserModel, user_id.value)
        if model is None:
            raise UserNotFound(user_id)
        model.password_hash = password_hash
