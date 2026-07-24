from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.sqlalchemy_identity_adapter import (
    SQLAlchemyIdentityAdapter,
)
from backend.core.infrastructure.auth.sqlalchemy_membership_adapter import (
    SQLAlchemyMembershipAdapter,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.session_scope import (
    run_in_session,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
def test_identity_state_survives_container_and_session_recreation(
    database_url: str,
    migrated_engine,
) -> None:
    email = f"persist-{uuid4()}@example.com"
    password = "restart-password"
    now = datetime.now(UTC)
    user = User(
        id=UserId(value=uuid4()),
        email=email,
        display_name="Persistent User",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    organization = Organization(
        id=OrganizationId(value=uuid4()),
        name=f"Persistent Org {uuid4()}",
        status=OrganizationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=user.id,
        organization_id=organization.id,
        status=MembershipStatus.ACTIVE,
        role=Role.auditor(),
        joined_at=now,
        updated_at=now,
    )

    first = create_container(
        AppSettings(
            app_name="SafetyMAIN API",
            app_version="0.1.0",
            app_env="test",
            database_url=database_url,
            cors_allowed_origins=(),
            jwt_secret_key="restart-persistence-secret-key-32b",
            jwt_issuer="safetymain-test",
            auth_enforcement=True,
        )
    )
    assert isinstance(first.identity_store, SQLAlchemyIdentityAdapter)
    assert isinstance(first.membership_store, SQLAlchemyMembershipAdapter)
    assert first.session_factory is not None

    password_hash = first.password_hasher.hash_password(password)

    def _seed_organization(session) -> None:
        SQLAlchemyOrganizationRepository(session).add(organization)

    run_in_session(first.session_factory, _seed_organization)
    first.identity_store.register_user(user, password_hash)
    first.membership_store.register_membership(membership)
    first.dispose()

    second = create_container(
        AppSettings(
            app_name="SafetyMAIN API",
            app_version="0.1.0",
            app_env="test",
            database_url=database_url,
            cors_allowed_origins=(),
            jwt_secret_key="restart-persistence-secret-key-32b",
            jwt_issuer="safetymain-test",
            auth_enforcement=True,
        )
    )
    try:
        loaded_user = second.user_lookup.get_user_by_email(email)
        assert loaded_user is not None
        assert loaded_user.id == user.id
        stored_hash = second.user_credentials.get_password_hash(user.id)
        assert stored_hash is not None
        assert second.password_hasher.verify_password(password, stored_hash)

        loaded_membership = second.membership_lookup.get_membership(
            user.id,
            organization.id,
        )
        assert loaded_membership is not None
        assert loaded_membership.role == Role.auditor()
        assert loaded_membership.grants_organization_access()
        assert second.membership_verification.is_active_member(
            user.id,
            organization.id,
        )
    finally:
        second.dispose()
