from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.membership import Membership
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryComplianceDocumentRepository,
    InMemoryDocumentTypeRepository,
    InMemoryHazardRepository,
    InMemoryInvitationRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryRiskAssessmentRepository,
    InMemoryRiskControlRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
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


def _headers(organization_id: OrganizationId, token: str) -> dict[str, str]:
    return {
        ORGANIZATION_ID_HEADER: str(organization_id.value),
        "Authorization": f"Bearer {token}",
    }


def _build_client(
    settings: AppSettings, *, role: Role
) -> tuple[object, OrganizationId, str, InMemoryDocumentTypeRepository]:
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    document_types = InMemoryDocumentTypeRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            organizations=organizations,
            memberships=memberships,
            invitations=InMemoryInvitationRepository(),
            hazards=InMemoryHazardRepository(),
            risk_assessments=InMemoryRiskAssessmentRepository(),
            risk_controls=InMemoryRiskControlRepository(),
            document_types=document_types,
            compliance_documents=InMemoryComplianceDocumentRepository(),
            audit_events=InMemoryAuditEventRepository(),
        )

    client, organization_id, access_token, user_id = build_enforced_client(
        settings, role=role
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
    stored = client.app.state.container.membership_store.get_membership(
        user_id, organization_id
    )
    assert stored is not None
    memberships.add(
        Membership(
            id=stored.id,
            user_id=stored.user_id,
            organization_id=stored.organization_id,
            status=stored.status,
            role=stored.role,
            joined_at=stored.joined_at or now,
            updated_at=now,
            revoked_at=stored.revoked_at,
        )
    )
    client.app.state.container.uow_factory = uow_factory
    return client, organization_id, access_token, document_types


def _active_type(org: OrganizationId, code: str) -> DocumentType:
    return DocumentType.create(
        organization_id=org,
        code=code,
        title_ru=f"Тип {code}",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=60,
        created_at=datetime.now(UTC),
    )


def test_list_document_types_scoped_to_organization(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, document_types = _build_client(
        enforced_auth_settings, role=Role.member()
    )
    document_types.add(_active_type(org, "iot_profession"))
    document_types.add(_active_type(org, "iot_work_type"))
    # Document type belonging to another organization must not leak.
    document_types.add(_active_type(OrganizationId(value=uuid4()), "foreign_type"))
    response = client.get(
        "/api/v1/document-types", headers=_headers(org, token)
    )
    assert response.status_code == 200
    codes = sorted(item["code"] for item in response.json()["items"])
    assert codes == ["iot_profession", "iot_work_type"]


def test_list_document_types_excludes_inactive_by_default(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, document_types = _build_client(
        enforced_auth_settings, role=Role.member()
    )
    active = _active_type(org, "iot_profession")
    inactive = _active_type(org, "iot_dormant")
    inactive_data = dict(inactive)
    inactive_data["is_active"] = False
    inactive = DocumentType(**inactive_data)
    document_types.add(active)
    document_types.add(inactive)
    response = client.get(
        "/api/v1/document-types", headers=_headers(org, token)
    )
    assert response.status_code == 200
    assert {item["code"] for item in response.json()["items"]} == {"iot_profession"}
    include_inactive = client.get(
        "/api/v1/document-types",
        headers=_headers(org, token),
        params={"include_inactive": "true"},
    )
    assert include_inactive.status_code == 200
    assert {item["code"] for item in include_inactive.json()["items"]} == {
        "iot_profession",
        "iot_dormant",
    }


def test_auditor_can_list_document_types(
    enforced_auth_settings: AppSettings,
) -> None:
    client, org, token, document_types = _build_client(
        enforced_auth_settings, role=Role.auditor()
    )
    document_types.add(_active_type(org, "iot_profession"))
    response = client.get(
        "/api/v1/document-types", headers=_headers(org, token)
    )
    assert response.status_code == 200
