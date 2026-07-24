from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from tests.api.contracts.assertions import assert_error_envelope
from tests.security.conftest import build_enforced_client

TEST_PASSWORD_SENTINEL = "TEST_PASSWORD_SENTINEL"
TEST_ACCESS_TOKEN_SENTINEL = "TEST_ACCESS_TOKEN_SENTINEL"
TEST_REFRESH_TOKEN_SENTINEL = "TEST_REFRESH_TOKEN_SENTINEL"


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


def _build_client(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[TestClient, OrganizationId, str, InMemoryAuditEventRepository, UserId]:
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


def _seed(
    audit_events: InMemoryAuditEventRepository,
    *,
    organization_id: OrganizationId,
    actor_user_id: UserId,
) -> AuditEvent:
    draft = AuditEvent(
        id=AuditEventId(value=uuid4()),
        actor_user_id=actor_user_id,
        authorization_organization_id=organization_id,
        target_organization_id=None,
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=uuid4(),
        outcome=AuditOutcome.SUCCESS,
        failure_code=None,
        metadata={"changed_fields": ["display_name"], "request_id": "req-integrity"},
        occurred_at=datetime.now(UTC),
    )
    audit_events.add(draft)
    return audit_events.get(draft.id)


def test_verify_valid_tenant_chain(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, token, audit_events, actor = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    first = _seed(audit_events, organization_id=organization_id, actor_user_id=actor)
    second = _seed(audit_events, organization_id=organization_id, actor_user_id=actor)

    response = client.get(
        "/api/v1/admin/audit-events/integrity",
        headers=_auth_headers(organization_id, token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == str(organization_id.value)
    assert body["valid"] is True
    assert body["checked_event_count"] == 2
    assert body["first_invalid_event_id"] is None
    assert body["reason"] is None

    listed = client.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(organization_id, token),
    )
    items = listed.json()["items"]
    by_id = {item["id"]: item for item in items}
    assert by_id[str(first.id.value)]["previous_integrity_hash"] is None
    assert by_id[str(first.id.value)]["integrity_hash"] == first.integrity_hash.value
    assert (
        by_id[str(second.id.value)]["previous_integrity_hash"]
        == first.integrity_hash.value
    )
    serialized = response.text + listed.text
    for sentinel in (
        TEST_PASSWORD_SENTINEL,
        TEST_ACCESS_TOKEN_SENTINEL,
        TEST_REFRESH_TOKEN_SENTINEL,
    ):
        assert sentinel not in serialized


def test_verify_excludes_other_organization_events(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, token, audit_events, actor = _build_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )
    _seed(audit_events, organization_id=organization_id, actor_user_id=actor)
    other = OrganizationId(value=uuid4())
    _seed(audit_events, organization_id=other, actor_user_id=actor)

    response = client.get(
        "/api/v1/admin/audit-events/integrity",
        headers=_auth_headers(organization_id, token),
    )
    assert response.status_code == 200
    assert response.json()["checked_event_count"] == 1


def test_verify_authorization_enforced(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, token, _, _ = _build_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    denied = client.get(
        "/api/v1/admin/audit-events/integrity",
        headers=_auth_headers(organization_id, token),
    )
    assert denied.status_code == 403
    assert_error_envelope(denied, status_code=403, code="permission_denied")

    unauthenticated = client.get("/api/v1/admin/audit-events/integrity")
    assert unauthenticated.status_code in {401, 403}


def test_verify_detects_tampered_stored_event(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, token, audit_events, actor = _build_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    event = _seed(audit_events, organization_id=organization_id, actor_user_id=actor)
    tampered = event.model_copy(update={"metadata": {"request_id": "tampered"}})
    audit_events._events_by_id[event.id] = tampered

    response = client.get(
        "/api/v1/admin/audit-events/integrity",
        headers=_auth_headers(organization_id, token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["first_invalid_event_id"] == str(event.id.value)
    assert body["reason"] == "event_hash_mismatch"
