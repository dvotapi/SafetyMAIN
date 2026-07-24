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
    InMemoryAuditEventRepository,
    InMemoryHazardRepository,
    InMemoryInvitationRepository,
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


def _payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "code": "HZ-100",
        "title": "Unguarded machine",
        "description": "Missing guard on conveyor",
        "category": "physical",
        "safety_directions": ["occupational_safety", "industrial_safety"],
        "source": "inspection",
        "affected_subjects": ["employee"],
        "location_reference": "Bay 3",
    }
    body.update(overrides)
    return body


def _build_client(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[
    TestClient,
    OrganizationId,
    str,
    UserId,
    InMemoryUnitOfWork,
    InMemoryHazardRepository,
    InMemoryAuditEventRepository,
]:
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    invitations = InMemoryInvitationRepository()
    hazards = InMemoryHazardRepository()
    audit_events = InMemoryAuditEventRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            organizations=organizations,
            memberships=memberships,
            invitations=invitations,
            hazards=hazards,
            audit_events=audit_events,
        )

    client, organization_id, access_token, user_id = build_enforced_client(
        settings,
        role=role,
    )
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
        uow_factory(),
        hazards,
        audit_events,
    )


def test_hazard_lifecycle_happy_path(enforced_auth_settings: AppSettings) -> None:
    client, org, token, _, _, hazards, audit_events = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(org, token)

    created = client.post("/api/v1/hazards", headers=headers, json=_payload())
    assert created.status_code == 201
    hazard = created.json()
    hazard_id = hazard["id"]
    assert hazard["status"] == "draft"
    assert hazard["version"] == 1

    updated = client.patch(
        f"/api/v1/hazards/{hazard_id}",
        headers=headers,
        json={"expected_version": 1, "title": "Updated conveyor hazard"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated conveyor hazard"
    assert updated.json()["version"] == 2

    activated = client.post(
        f"/api/v1/hazards/{hazard_id}/activate",
        headers=headers,
        json={"expected_version": 2},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    repeated = client.post(
        f"/api/v1/hazards/{hazard_id}/activate",
        headers=headers,
        json={"expected_version": 3},
    )
    assert repeated.status_code == 409
    assert_error_envelope(repeated, status_code=409, code="hazard_already_active")

    archived = client.post(
        f"/api/v1/hazards/{hazard_id}/archive",
        headers=headers,
        json={"expected_version": 3, "reason": "No longer present"},
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    listed = client.get("/api/v1/hazards", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] == 0

    by_id = client.get(f"/api/v1/hazards/{hazard_id}", headers=headers)
    assert by_id.status_code == 200
    assert by_id.json()["status"] == "archived"

    restored = client.post(
        f"/api/v1/hazards/{hazard_id}/restore",
        headers=headers,
        json={"expected_version": 4, "reason": "Still relevant"},
    )
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"
    assert len(hazards.snapshot()) == 1
    assert any(
        event.action.value.startswith("safety.hazard.")
        for event in audit_events.snapshot().values()
    )


def test_member_cannot_activate_and_auditor_read_only(
    enforced_auth_settings: AppSettings,
) -> None:
    member_client, org, member_token, _, _, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _auth_headers(org, member_token)
    created = member_client.post("/api/v1/hazards", headers=headers, json=_payload())
    assert created.status_code == 201
    hazard_id = created.json()["id"]
    activate = member_client.post(
        f"/api/v1/hazards/{hazard_id}/activate",
        headers=headers,
        json={"expected_version": 1},
    )
    assert activate.status_code == 403

    auditor_client, auditor_org, auditor_token, _, _, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )
    # Cross-org masked as 404
    cross = auditor_client.get(
        f"/api/v1/hazards/{hazard_id}",
        headers=_auth_headers(auditor_org, auditor_token),
    )
    assert cross.status_code == 404


def test_duplicate_code_and_version_conflict(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, _, _, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(org, token)
    assert client.post("/api/v1/hazards", headers=headers, json=_payload()).status_code == 201
    duplicate = client.post("/api/v1/hazards", headers=headers, json=_payload())
    assert duplicate.status_code == 409
    assert_error_envelope(duplicate, status_code=409, code="duplicate_hazard_code")

    created = client.post(
        "/api/v1/hazards",
        headers=headers,
        json=_payload(code="HZ-200"),
    )
    hazard_id = created.json()["id"]
    conflict = client.patch(
        f"/api/v1/hazards/{hazard_id}",
        headers=headers,
        json={"expected_version": 99, "title": "Nope"},
    )
    assert conflict.status_code == 409
    assert_error_envelope(conflict, status_code=409, code="hazard_version_conflict")


def test_unauthenticated_hazard_access_rejected(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, _, _, _, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    response = client.get(
        "/api/v1/hazards",
        headers={ORGANIZATION_ID_HEADER: str(org.value)},
    )
    assert response.status_code == 401
