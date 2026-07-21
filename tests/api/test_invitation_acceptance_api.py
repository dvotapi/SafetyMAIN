from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.invitation_lifecycle import CreateInvitationCommand
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.create_invitation import CreateInvitationHandler
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryInvitationRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from backend.core.infrastructure.time.utc_clock import UtcClock
from tests.api.contracts.assertions import assert_error_envelope
from tests.core.audit_test_support import make_admin_audit_stack


@pytest.fixture
def enforced_auth_settings() -> AppSettings:
    return AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url=None,
        jwt_secret_key="test-secret-key-with-sufficient-length",
        jwt_algorithm="HS256",
        jwt_access_token_ttl_seconds=3600,
        jwt_refresh_token_ttl_seconds=604800,
        jwt_issuer="safetymain",
        auth_enforcement=True,
    )


def _build_acceptance_client(
    settings: AppSettings,
) -> tuple[TestClient, str, str, User, OrganizationId, InMemoryMembershipRepository]:
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    invitations = InMemoryInvitationRepository()
    identity_store = InMemoryIdentityStore()
    membership_store = InMemoryMembershipStore()
    container = create_container(
        settings,
        identity_store=identity_store,
        membership_store=membership_store,
    )

    auth_org = OrganizationId(value=uuid4())
    target_org = OrganizationId(value=uuid4())
    now = datetime.now(UTC)
    organizations.add(
        Organization(
            id=auth_org,
            name="Auth Org",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    organizations.add(
        Organization(
            id=target_org,
            name="Target Org",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )

    admin = User(
        id=UserId(value=uuid4()),
        display_name="Admin",
        email="admin@example.com",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    invitee = User(
        id=UserId(value=uuid4()),
        display_name="Invitee",
        email="invitee@example.com",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    users.add(admin)
    users.add(invitee)
    identity_store.register_user(admin, container.password_hasher.hash_password("admin-pass"))
    identity_store.register_user(
        invitee,
        container.password_hasher.hash_password("invitee-pass"),
    )
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=admin.id,
            organization_id=auth_org,
            status=MembershipStatus.ACTIVE,
            role=Role.admin(),
            joined_at=now,
            updated_at=now,
        )
    )

    stack = make_admin_audit_stack(
        users=users,
        organizations=organizations,
        memberships=memberships,
        invitations=invitations,
    )

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            organizations=organizations,
            memberships=memberships,
            invitations=invitations,
            audit_events=stack.audit_events,
        )

    container.uow_factory = uow_factory
    client = TestClient(create_app(settings=settings, container=container))

    create_result = CreateInvitationHandler(
        stack.uow,
        UtcClock(),
        stack.audit,
    ).handle(
        CreateInvitationCommand(
            organization_id=target_org,
            email=invitee.email,
            role=Role.member(),
            created_by=admin.id,
            audit_context=AuditContext(
                actor_user_id=admin.id,
                authorization_organization_id=auth_org,
            ),
        )
    )

    auth_handler = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    )
    invitee_tokens = auth_handler.handle(
        AuthenticateUserCommand(email=invitee.email, password="invitee-pass")
    )

    return (
        client,
        create_result.token,
        invitee_tokens.access_token,
        invitee,
        target_org,
        memberships,
    )


def test_authenticated_matching_user_can_accept_invitation(
    enforced_auth_settings: AppSettings,
) -> None:
    client, token, access_token, invitee, target_org, memberships = _build_acceptance_client(
        enforced_auth_settings
    )

    response = client.post(
        "/api/v1/invitations/accept",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"token": token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ACCEPTED"
    membership = memberships.get_by_user_and_organization(invitee.id, target_org)
    assert membership is not None
    assert membership.is_active() is True


def test_unauthenticated_acceptance_is_denied(enforced_auth_settings: AppSettings) -> None:
    client, token, _, _, _, _ = _build_acceptance_client(enforced_auth_settings)

    response = client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")
