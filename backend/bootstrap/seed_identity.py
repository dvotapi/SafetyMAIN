from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from backend.core.contracts.password_hasher import PasswordHasherContract
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.sqlalchemy_identity_adapter import SQLAlchemyIdentityAdapter
from backend.core.infrastructure.auth.sqlalchemy_membership_adapter import (
    SQLAlchemyMembershipAdapter,
)
from backend.core.domain.exceptions import OrganizationNotFound
from backend.core.infrastructure.persistence.sqlalchemy.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.session_scope import run_in_session

DEVELOPMENT_ORGANIZATION_ID = UUID("11111111-1111-1111-1111-111111111111")
DEVELOPMENT_ADMIN_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
DEVELOPMENT_MEMBER_USER_ID = UUID("33333333-3333-3333-3333-333333333333")
DEVELOPMENT_AUDITOR_USER_ID = UUID("44444444-4444-4444-4444-444444444444")
DEVELOPMENT_ADMIN_MEMBERSHIP_ID = UUID("55555555-5555-5555-5555-555555555555")
DEVELOPMENT_MEMBER_MEMBERSHIP_ID = UUID("66666666-6666-6666-6666-666666666666")
DEVELOPMENT_AUDITOR_MEMBERSHIP_ID = UUID("77777777-7777-7777-7777-777777777777")

DEFAULT_DEVELOPMENT_PASSWORD = "dev-password"


def seed_development_identity(
    session_factory: sessionmaker[Session],
    *,
    password_hasher: PasswordHasherContract,
    password: str = DEFAULT_DEVELOPMENT_PASSWORD,
) -> None:
    """Seed development users and memberships. Never call automatically in production."""

    now = datetime.now(UTC)
    organization = Organization(
        id=OrganizationId(value=DEVELOPMENT_ORGANIZATION_ID),
        name="SafetyMAIN Development Organization",
        status=OrganizationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    def _seed_organization(session: Session) -> None:
        repository = SQLAlchemyOrganizationRepository(session)
        try:
            repository.get(organization.id)
        except OrganizationNotFound:
            repository.add(organization)

    run_in_session(session_factory, _seed_organization)

    password_hash = password_hasher.hash_password(password)
    identity_adapter = SQLAlchemyIdentityAdapter(session_factory)
    membership_adapter = SQLAlchemyMembershipAdapter(session_factory)

    users = (
        (
            DEVELOPMENT_ADMIN_USER_ID,
            "Development Admin",
            "admin@example.com",
            Role.admin(),
            DEVELOPMENT_ADMIN_MEMBERSHIP_ID,
        ),
        (
            DEVELOPMENT_MEMBER_USER_ID,
            "Development Member",
            "member@example.com",
            Role.member(),
            DEVELOPMENT_MEMBER_MEMBERSHIP_ID,
        ),
        (
            DEVELOPMENT_AUDITOR_USER_ID,
            "Development Auditor",
            "auditor@example.com",
            Role.auditor(),
            DEVELOPMENT_AUDITOR_MEMBERSHIP_ID,
        ),
    )

    for user_id, display_name, email, role, membership_id in users:
        if identity_adapter.get_user_by_email(email) is not None:
            continue

        user = User(
            id=UserId(value=user_id),
            display_name=display_name,
            email=email,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        identity_adapter.register_user(user, password_hash)
        membership_adapter.register_membership(
            Membership(
                id=MembershipId(value=membership_id),
                user_id=user.id,
                organization_id=organization.id,
                status=MembershipStatus.ACTIVE,
                role=role,
                joined_at=now,
            )
        )
