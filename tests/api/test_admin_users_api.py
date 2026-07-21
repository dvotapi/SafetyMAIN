from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
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
) -> tuple[TestClient, OrganizationId, str, InMemoryUserRepository]:
    users = InMemoryUserRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
        )

    client, organization_id, access_token, _ = build_enforced_client(settings, role=role)
    client.app.state.container.uow_factory = uow_factory
    return client, organization_id, access_token, users


def test_admin_can_create_user(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, users = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )

    response = client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
        json={
            "email": "new-user@example.com",
            "display_name": "New User",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-user@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert len(users._users_by_id) == 1


def test_auditor_can_list_users_but_not_create(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )

    list_response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )
    create_response = client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
        json={
            "email": "blocked@example.com",
            "display_name": "Blocked",
        },
    )

    assert list_response.status_code == 200
    assert create_response.status_code == 403
    assert_error_envelope(create_response, status_code=403, code="permission_denied")


def test_member_is_denied_admin_user_access(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_duplicate_email_returns_409(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)
    payload = {
        "email": "duplicate@example.com",
        "display_name": "Duplicate User",
    }

    first = client.post("/api/v1/admin/users", headers=headers, json=payload)
    second = client.post("/api/v1/admin/users", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert_error_envelope(second, status_code=409, code="duplicate_user_email")


def test_list_users_supports_filtering_and_pagination(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, users = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    now = datetime.now(UTC)
    users.add(
        User(
            id=UserId(value=uuid4()),
            display_name="Alpha Operator",
            email="alpha@example.com",
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    users.add(
        User(
            id=UserId(value=uuid4()),
            display_name="Beta Operator",
            email="beta@example.com",
            status=UserStatus.DEACTIVATED,
            created_at=now,
            updated_at=now,
        )
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
        params={"email": "alpha", "is_active": True, "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["email"] == "alpha@example.com"


def test_missing_bearer_token_is_rejected(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, _, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers={ORGANIZATION_ID_HEADER: str(organization_id.value)},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")
