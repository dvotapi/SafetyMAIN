from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.value_objects import OrganizationId, Role
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryOrganizationRepository,
    InMemoryUnitOfWork,
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
) -> tuple[TestClient, OrganizationId, str, InMemoryOrganizationRepository]:
    organizations = InMemoryOrganizationRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            organizations=organizations,
        )

    client, organization_id, access_token, _ = build_enforced_client(settings, role=role)
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
    client.app.state.container.uow_factory = uow_factory
    return client, organization_id, access_token, organizations


def test_admin_can_create_organization(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token, organizations = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )

    response = client.post(
        "/api/v1/admin/organizations",
        headers=_auth_headers(organization_id, access_token),
        json={"name": "New Organization", "is_active": True},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "New Organization"
    assert body["is_active"] is True
    assert len(organizations._organizations_by_id) == 2


def test_auditor_can_list_organizations_but_not_create(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )

    list_response = client.get(
        "/api/v1/admin/organizations",
        headers=_auth_headers(organization_id, access_token),
    )
    create_response = client.post(
        "/api/v1/admin/organizations",
        headers=_auth_headers(organization_id, access_token),
        json={"name": "Blocked Organization"},
    )

    assert list_response.status_code == 200
    assert create_response.status_code == 403
    assert_error_envelope(create_response, status_code=403, code="permission_denied")


def test_member_is_denied_admin_organization_access(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/organizations",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_duplicate_organization_name_returns_409(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)

    first = client.post(
        "/api/v1/admin/organizations",
        headers=headers,
        json={"name": "Acme Safety"},
    )
    second = client.post(
        "/api/v1/admin/organizations",
        headers=headers,
        json={"name": " acme safety "},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert_error_envelope(second, status_code=409, code="duplicate_organization_name")


def test_deactivate_current_authorization_organization_returns_409(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)

    response = client.post(
        f"/api/v1/admin/organizations/{organization_id.value}/deactivate",
        headers=headers,
    )

    assert response.status_code == 409
    assert_error_envelope(
        response,
        status_code=409,
        code="current_organization_deactivation",
    )


def test_list_organizations_supports_filtering(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, organizations = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    now = datetime.now(UTC)
    organizations.add(
        Organization(
            id=OrganizationId(value=uuid4()),
            name="Alpha Organization",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    organizations.add(
        Organization(
            id=OrganizationId(value=uuid4()),
            name="Beta Organization",
            status=OrganizationStatus.DEACTIVATED,
            created_at=now,
            updated_at=now,
        )
    )

    response = client.get(
        "/api/v1/admin/organizations",
        headers=_auth_headers(organization_id, access_token),
        params={"name": "Alpha", "is_active": True, "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["name"] == "Alpha Organization"


def test_get_organization_returns_404_for_missing_id(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )

    response = client.get(
        f"/api/v1/admin/organizations/{uuid4()}",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 404
    assert_error_envelope(response, status_code=404, code="organization_not_found")


def test_missing_bearer_token_is_rejected(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, _, _ = _build_admin_client(
        enforced_auth_settings,
        role=Role.admin(),
    )

    response = client.get(
        "/api/v1/admin/organizations",
        headers={ORGANIZATION_ID_HEADER: str(organization_id.value)},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")
