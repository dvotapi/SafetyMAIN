from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.audit_event_list_criteria import AuditEventListCriteria
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from backend.core.domain.entities.audit_event import AuditEvent
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


def _build_audit_client(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[
    TestClient,
    OrganizationId,
    str,
    InMemoryAuditEventRepository,
    UserId,
]:
    audit_events = InMemoryAuditEventRepository()
    users = InMemoryUserRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            audit_events=audit_events,
        )

    client, organization_id, access_token, actor_user_id = build_enforced_client(
        settings,
        role=role,
    )
    client.app.state.container.uow_factory = uow_factory
    return client, organization_id, access_token, audit_events, actor_user_id


def _seed_success_event(
    audit_events: InMemoryAuditEventRepository,
    *,
    scope_organization_id: OrganizationId,
    actor_user_id: UserId,
) -> AuditEvent:
    event = AuditEvent(
        id=AuditEventId(value=uuid4()),
        actor_user_id=actor_user_id,
        authorization_organization_id=scope_organization_id,
        target_organization_id=None,
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=uuid4(),
        outcome=AuditOutcome.SUCCESS,
        failure_code=None,
        metadata={"changed_fields": ["display_name"]},
        occurred_at=datetime.now(UTC),
    )
    audit_events.add(event)
    return event


def test_admin_can_list_audit_events(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    event = _seed_success_event(
        audit_events,
        scope_organization_id=organization_id,
        actor_user_id=actor_user_id,
    )

    response = client.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["id"] == str(event.id.value)
    assert "token" not in response.text.lower()


def test_auditor_can_read_audit_events(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )
    _seed_success_event(
        audit_events,
        scope_organization_id=organization_id,
        actor_user_id=actor_user_id,
    )

    response = client.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 200


def test_member_is_denied_audit_access(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _, _ = _build_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_cross_organization_audit_event_is_masked_as_not_found(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    other_scope = OrganizationId(value=uuid4())
    event = _seed_success_event(
        audit_events,
        scope_organization_id=other_scope,
        actor_user_id=actor_user_id,
    )

    response = client.get(
        f"/api/v1/admin/audit-events/{event.id.value}",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 404
    assert_error_envelope(response, status_code=404, code="audit_event_not_found")


def test_create_user_records_audit_event_without_sensitive_fields(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)

    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "email": "audited-user@example.com",
            "display_name": "Audited User",
        },
    )

    assert response.status_code == 201
    listed = client.get("/api/v1/admin/audit-events", headers=headers)
    assert listed.status_code == 200
    payload = listed.json()["items"][0]
    serialized = str(payload)
    for forbidden in (
        "password",
        "token_hash",
        "Bearer",
        "jwt",
        "secret-password",
    ):
        assert forbidden not in serialized

    events = audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    )
    assert events.total == 1
    assert events.items[0].actor_user_id == actor_user_id
