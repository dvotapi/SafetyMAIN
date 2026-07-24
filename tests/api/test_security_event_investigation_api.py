from __future__ import annotations

from datetime import UTC, datetime, timedelta
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


def _build_audit_client(
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


def _add_event(
    audit_events: InMemoryAuditEventRepository,
    *,
    scope: OrganizationId,
    action: AuditAction,
    outcome: AuditOutcome,
    actor_user_id: UserId | None = None,
    request_id: str | None = None,
    occurred_at: datetime | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    payload = dict(metadata or {})
    if request_id is not None:
        payload["request_id"] = request_id
    resource_type = (
        AuditResourceType.SESSION
        if action.value.startswith("authentication.")
        else AuditResourceType.USER
    )
    if action is AuditAction.AUTHORIZATION_PERMISSION_DENIED:
        resource_type = AuditResourceType.USER
    event = AuditEvent(
        id=AuditEventId(value=uuid4()),
        actor_user_id=actor_user_id,
        authorization_organization_id=scope,
        target_organization_id=None,
        action=action,
        resource_type=resource_type,
        resource_id=uuid4(),
        outcome=outcome,
        failure_code="invalid_credentials" if outcome is AuditOutcome.FAILURE else None,
        metadata=payload,
        occurred_at=occurred_at or datetime.now(UTC),
    )
    audit_events.add(event)
    return event


def test_list_authentication_investigation_filters(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    base = datetime(2026, 7, 24, 8, 0, tzinfo=UTC)
    failed_login = _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.AUTHENTICATION_LOGIN_FAILED,
        outcome=AuditOutcome.FAILURE,
        actor_user_id=actor_user_id,
        request_id="req-auth-fail",
        occurred_at=base,
    )
    _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED,
        outcome=AuditOutcome.SUCCESS,
        actor_user_id=actor_user_id,
        request_id="req-auth-ok",
        occurred_at=base + timedelta(minutes=1),
    )
    _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.AUTHENTICATION_REFRESH_FAILED,
        outcome=AuditOutcome.FAILURE,
        actor_user_id=None,
        request_id="req-refresh-fail",
        occurred_at=base + timedelta(minutes=2),
    )
    _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.USER_CREATE,
        outcome=AuditOutcome.SUCCESS,
        actor_user_id=actor_user_id,
        request_id="req-auth-fail",
        occurred_at=base,
    )

    headers = _auth_headers(organization_id, access_token)
    by_name = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"event_name": "authentication.login.failed"},
    )
    by_category = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={
            "event_category": "AUTHENTICATION",
            "outcome": "FAILURE",
            "actor_user_id": str(actor_user_id.value),
            "request_id": "req-auth-fail",
            "occurred_from": base.isoformat().replace("+00:00", "Z"),
            "occurred_to": (base + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        },
    )
    by_severity = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"severity": "MEDIUM", "event_category": "AUTHENTICATION"},
    )

    assert by_name.status_code == 200
    assert by_name.json()["pagination"]["total"] == 1
    item = by_name.json()["items"][0]
    assert item["id"] == str(failed_login.id.value)
    assert item["event_name"] == "authentication.login.failed"
    assert item["event_category"] == "AUTHENTICATION"
    assert item["severity"] == "MEDIUM"
    assert item["request_id"] == "req-auth-fail"

    assert by_category.status_code == 200
    assert by_category.json()["pagination"]["total"] == 1
    assert by_category.json()["items"][0]["id"] == str(failed_login.id.value)

    assert by_severity.status_code == 200
    names = {entry["event_name"] for entry in by_severity.json()["items"]}
    assert names == {
        "authentication.login.failed",
        "authentication.refresh.failed",
    }


def test_permission_denial_and_admin_events_remain_queryable(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.AUTHORIZATION_PERMISSION_DENIED,
        outcome=AuditOutcome.FAILURE,
        actor_user_id=actor_user_id,
        request_id="req-denial",
    )
    _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.USER_CREATE,
        outcome=AuditOutcome.SUCCESS,
        actor_user_id=actor_user_id,
    )
    headers = _auth_headers(organization_id, access_token)

    denial = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"event_name": "authorization.permission_denied"},
    )
    admin = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"action": "user.create"},
    )

    assert denial.status_code == 200
    assert denial.json()["pagination"]["total"] == 1
    assert admin.status_code == 200
    assert admin.json()["pagination"]["total"] == 1


def test_investigation_validation_errors(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _, _ = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)

    unknown = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"event_name": "authentication.login.unknown"},
    )
    empty_request = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"request_id": "   "},
    )
    overlong = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"request_id": "x" * 129},
    )
    inverted = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={
            "occurred_from": "2026-07-24T12:00:00Z",
            "occurred_to": "2026-07-24T11:00:00Z",
        },
    )
    naive = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"occurred_from": "2026-07-24T12:00:00"},
    )
    bad_actor = client.get(
        "/api/v1/admin/audit-events",
        headers=headers,
        params={"actor_user_id": "not-a-uuid"},
    )

    for response in (unknown, empty_request, overlong, inverted, naive, bad_actor):
        assert response.status_code == 422
        assert_error_envelope(response, status_code=422, code="request_validation_error")


def test_cross_tenant_request_id_does_not_leak(
    enforced_auth_settings: AppSettings,
) -> None:
    client_a, org_a, token_a, audit_events, actor_a = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    client_b, org_b, token_b, _, actor_b = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    # Share the same repository store with both clients for collision simulation.
    def shared_uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=InMemoryUserRepository(),
            audit_events=audit_events,
        )

    client_a.app.state.container.uow_factory = shared_uow_factory
    client_b.app.state.container.uow_factory = shared_uow_factory

    shared_request_id = "req-cross-tenant"
    event_a = _add_event(
        audit_events,
        scope=org_a,
        action=AuditAction.AUTHENTICATION_LOGIN_FAILED,
        outcome=AuditOutcome.FAILURE,
        actor_user_id=actor_a,
        request_id=shared_request_id,
    )
    _add_event(
        audit_events,
        scope=org_b,
        action=AuditAction.AUTHENTICATION_LOGIN_FAILED,
        outcome=AuditOutcome.FAILURE,
        actor_user_id=actor_b,
        request_id=shared_request_id,
    )

    response_a = client_a.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(org_a, token_a),
        params={"request_id": shared_request_id},
    )
    response_b = client_b.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(org_b, token_b),
        params={"request_id": shared_request_id},
    )

    assert response_a.status_code == 200
    assert response_a.json()["pagination"]["total"] == 1
    assert response_a.json()["items"][0]["id"] == str(event_a.id.value)
    assert response_b.status_code == 200
    assert response_b.json()["pagination"]["total"] == 1
    assert response_b.json()["items"][0]["id"] != str(event_a.id.value)


def test_investigation_response_excludes_sensitive_sentinels(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    _add_event(
        audit_events,
        scope=organization_id,
        action=AuditAction.AUTHENTICATION_LOGIN_FAILED,
        outcome=AuditOutcome.FAILURE,
        actor_user_id=actor_user_id,
        request_id="req-sensitive",
        metadata={
            "request_id": "req-sensitive",
            "authentication_method": "password",
        },
    )
    response = client.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(organization_id, access_token),
        params={"event_category": "AUTHENTICATION"},
    )
    serialized = response.text
    assert response.status_code == 200
    assert TEST_PASSWORD_SENTINEL not in serialized
    assert TEST_ACCESS_TOKEN_SENTINEL not in serialized
    assert TEST_REFRESH_TOKEN_SENTINEL not in serialized
    assert "password_hash" not in serialized
