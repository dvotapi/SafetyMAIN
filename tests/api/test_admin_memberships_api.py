from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.membership import Membership
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from tests.api.contracts.assertions import assert_error_envelope
from tests.security.conftest import build_enforced_client


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


def _auth_headers(organization_id: OrganizationId, access_token: str) -> dict[str, str]:
    return {
        ORGANIZATION_ID_HEADER: str(organization_id.value),
        "Authorization": f"Bearer {access_token}",
    }


def _build_admin_client(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[
    TestClient,
    OrganizationId,
    str,
    UserId,
    InMemoryUnitOfWork,
    InMemoryMembershipRepository,
    InMemoryUserRepository,
    InMemoryOrganizationRepository,
]:
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            organizations=organizations,
            memberships=memberships,
        )

    client, organization_id, access_token, user_id = build_enforced_client(
        settings,
        role=role,
    )
    uow = uow_factory()
    now = datetime.now(UTC)
    organizations.add(
        Organization(
            id=organization_id,
            name="Authorization Organization",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    users.add(
        User(
            id=user_id,
            display_name="Safety Operator",
            email=f"operator-{uuid4()}@example.com",
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    stored_membership = client.app.state.container.membership_store.get_membership(
        user_id,
        organization_id,
    )
    assert stored_membership is not None
    memberships.add(
        Membership(
            id=stored_membership.id,
            user_id=stored_membership.user_id,
            organization_id=stored_membership.organization_id,
            status=stored_membership.status,
            role=stored_membership.role,
            joined_at=stored_membership.joined_at or now,
            updated_at=now,
            revoked_at=stored_membership.revoked_at,
        )
    )

    client.app.state.container.uow_factory = uow_factory
    return (
        client,
        organization_id,
        access_token,
        user_id,
        uow,
        memberships,
        users,
        organizations,
    )


def test_admin_can_create_membership(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _, _, memberships, users, organizations = (
        _build_admin_client(enforced_auth_settings, role=Role.admin())
    )
    now = datetime.now(UTC)
    target_user = User(
        id=UserId(value=uuid4()),
        display_name="Member User",
        email="member@example.com",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    users.add(target_user)

    response = client.post(
        "/api/v1/admin/memberships",
        headers=_auth_headers(organization_id, access_token),
        json={
            "user_id": str(target_user.id.value),
            "organization_id": str(organization_id.value),
            "role": "member",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == str(target_user.id.value)
    assert body["role"] == "member"
    assert len(memberships._memberships_by_id) >= 2


def test_auditor_can_list_but_not_create_memberships(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _, _, _, _, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )

    list_response = client.get(
        "/api/v1/admin/memberships",
        headers=_auth_headers(organization_id, access_token),
        params={"organization_id": str(organization_id.value)},
    )
    create_response = client.post(
        "/api/v1/admin/memberships",
        headers=_auth_headers(organization_id, access_token),
        json={
            "user_id": str(uuid4()),
            "organization_id": str(organization_id.value),
            "role": "member",
        },
    )

    assert list_response.status_code == 200
    assert create_response.status_code == 403
    assert_error_envelope(create_response, status_code=403, code="permission_denied")


def test_member_is_denied_admin_membership_access(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _, _, _, _, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/memberships",
        headers=_auth_headers(organization_id, access_token),
        params={"organization_id": str(organization_id.value)},
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_duplicate_membership_returns_409(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _, _, memberships, users, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    now = datetime.now(UTC)
    target_user = User(
        id=UserId(value=uuid4()),
        display_name="Member User",
        email="duplicate@example.com",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    users.add(target_user)
    headers = _auth_headers(organization_id, access_token)
    payload = {
        "user_id": str(target_user.id.value),
        "organization_id": str(organization_id.value),
        "role": "member",
    }

    first = client.post("/api/v1/admin/memberships", headers=headers, json=payload)
    second = client.post("/api/v1/admin/memberships", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert_error_envelope(second, status_code=409, code="duplicate_membership")


def test_self_deactivation_returns_409(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, user_id, _, memberships, _, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    auth_membership = memberships.get_by_user_and_organization(user_id, organization_id)
    assert auth_membership is not None

    response = client.post(
        f"/api/v1/admin/memberships/{auth_membership.id.value}/deactivate",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 409
    assert_error_envelope(response, status_code=409, code="self_membership_deactivation")
