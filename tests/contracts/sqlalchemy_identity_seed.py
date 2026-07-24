from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions.organization import OrganizationNotFound
from backend.core.domain.exceptions.user import UserNotFound
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.infrastructure.persistence.sqlalchemy.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.user_repository import (
    SQLAlchemyUserRepository,
)


def ensure_organization(session: Session, organization_id: OrganizationId) -> None:
    repository = SQLAlchemyOrganizationRepository(session)
    try:
        repository.get(organization_id)
    except OrganizationNotFound:
        now = datetime.now(UTC)
        repository.add(
            Organization(
                id=organization_id,
                name=f"Contract Org {organization_id.value}",
                status=OrganizationStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        session.flush()


def ensure_user(session: Session, user_id: UserId) -> None:
    repository = SQLAlchemyUserRepository(session)
    try:
        repository.get(user_id)
    except UserNotFound:
        now = datetime.now(UTC)
        repository.add(
            User(
                id=user_id,
                email=f"contract-{user_id.value}@example.com",
                display_name=f"Contract User {user_id.value}",
                status=UserStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        session.flush()
