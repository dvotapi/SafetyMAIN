from __future__ import annotations

from datetime import UTC, datetime

from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.persistence.sqlalchemy.models.user_model import UserModel


def to_model(user: User, *, password_hash: str) -> UserModel:
    now = datetime.now(UTC)
    return UserModel(
        id=user.id.value,
        email=user.email,
        password_hash=password_hash,
        display_name=user.display_name,
        is_active=user.is_active(),
        external_subject=user.external_subject,
        created_at=user.created_at,
        updated_at=now,
    )


def apply_to_model(model: UserModel, user: User) -> None:
    model.email = user.email
    model.display_name = user.display_name
    model.is_active = user.is_active()
    model.external_subject = user.external_subject
    model.updated_at = datetime.now(UTC)


def to_domain(model: UserModel) -> User:
    return User(
        id=UserId(value=model.id),
        display_name=model.display_name,
        email=model.email,
        status=UserStatus.ACTIVE if model.is_active else UserStatus.DEACTIVATED,
        external_subject=model.external_subject,
        created_at=model.created_at,
    )
