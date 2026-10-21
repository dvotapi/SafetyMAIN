from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.membership import Membership
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentSource,
    ComplianceDocumentStatus,
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
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


def _headers(organization_id: OrganizationId, token: str) -> dict[str, str]:
    return {
        ORGANIZATION_ID_HEADER: str(organization_id.value),
        "Authorization": f"Bearer {token}",
    }


def _seed_type(
    organization_id: OrganizationId,
    *,
    code: str = "iot_profession",
    review_period_months: int | None = 60,
    requires_approval_order: bool = False,
    is_active: bool = True,
) -> DocumentType:
    return DocumentType.create(
        organization_id=organization_id,
        code=code,
        title_ru="ИОТ по профессии",
        safety_domain=SafetyDomain.OCCUPATIONAL,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=review_period_months,
        requires_approval_order=requires_approval_order,
        is_active=is_active,
        created_at=datetime.now(UTC),
    )


def _build_client(settings: AppSettings, *, role: Role) -> dict[str, Any]:
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    invitations = InMemoryInvitationRepository()
    hazards = InMemoryHazardRepository()
    risk_assessments = InMemoryRiskAssessmentRepository()
    risk_controls = InMemoryRiskControlRepository()
    document_types = InMemoryDocumentTypeRepository()
    compliance_documents = InMemoryComplianceDocumentRepository()
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
            risk_assessments=risk_assessments,
            risk_controls=risk_controls,
            document_types=document_types,
            compliance_documents=compliance_documents,
            audit_events=audit_events,
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
    document_type = _seed_type(organization_id)
    document_types.add(document_type)
    return {
        "client": client,
        "organization_id": organization_id,
        "token": access_token,
        "user_id": user_id,
        "document_type": document_type,
        "document_types": document_types,
        "compliance_documents": compliance_documents,
        "audit_events": audit_events,
    }


def _create_payload(
    *, document_type_id: UUID, code: str = "CD-001", title: str = "Local Act"
) -> dict[str, object]:
    return {
        "document_type_id": str(document_type_id),
        "code": code,
        "title": title,
        "applicability": {
            "positions": ["welder", "driver"],
            "work_types": ["hot work"],
            "departments": [],
            "asset_ids": [],
        },
        "notes": "initial",
    }


def test_create_and_get_compliance_document(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    created = ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(document_type_id=ctx["document_type"].id.value),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "draft"
    assert body["version"] == 1
    assert body["is_review_due"] is False
    assert body["applicability"]["positions"] == ["welder", "driver"]
    assert body["current_file"] is None
    assert "Location" in created.headers

    got = ctx["client"].get(
        f"/api/v1/compliance-documents/{body['id']}", headers=headers
    )
    assert got.status_code == 200
    assert got.json()["code"] == "CD-001"
    assert any(
        event.action.value == "compliance.document.created"
        for event in ctx["audit_events"].snapshot().values()
    )


def test_update_compliance_document_version_and_fields(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    created = ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(document_type_id=ctx["document_type"].id.value),
    )
    document_id = created.json()["id"]
    updated = ctx["client"].patch(
        f"/api/v1/compliance-documents/{document_id}",
        headers=headers,
        json={
            "expected_version": 1,
            "title": "Updated title",
            "effective_from": "2026-01-01",
            "notes": "revised",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated title"
    assert updated.json()["effective_from"] == "2026-01-01"
    assert updated.json()["version"] == 2

    stale = ctx["client"].patch(
        f"/api/v1/compliance-documents/{document_id}",
        headers=headers,
        json={"expected_version": 1, "title": "Stale"},
    )
    assert_error_envelope(
        stale, status_code=409, code="compliance_document_version_conflict"
    )


def test_update_rejected_when_not_draft(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    now = datetime.now(UTC)
    document = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=ctx["document_type"],
        code="CD-NOT-DRAFT",
        title="Already active",
        created_by=ctx["user_id"],
        created_at=now,
    ).model_copy(update={"status": ComplianceDocumentStatus.ACTIVE})
    ctx["compliance_documents"].add(document)
    response = ctx["client"].patch(
        f"/api/v1/compliance-documents/{document.id.value}",
        headers=headers,
        json={"expected_version": 1, "title": "Try to edit"},
    )
    assert_error_envelope(
        response, status_code=422, code="compliance_document_cannot_be_modified"
    )


def test_create_with_unknown_document_type_is_404(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    response = ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(document_type_id=uuid4(), code="CD-404"),
    )
    assert_error_envelope(response, status_code=404, code="document_type_not_found")


def test_create_with_inactive_document_type_is_422(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    inactive = _seed_type(
        ctx["organization_id"], code="iot_inactive", is_active=False
    )
    ctx["document_types"].add(inactive)
    headers = _headers(ctx["organization_id"], ctx["token"])
    response = ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(document_type_id=inactive.id.value, code="CD-INACT"),
    )
    assert_error_envelope(
        response, status_code=422, code="compliance_document_validation_error"
    )


def test_create_with_invalid_applicability_is_422(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    payload = _create_payload(
        document_type_id=ctx["document_type"].id.value, code="CD-BAD"
    )
    payload["applicability"] = {"positions": [""]}
    response = ctx["client"].post(
        "/api/v1/compliance-documents", headers=headers, json=payload
    )
    assert response.status_code == 422


def test_cross_tenant_access_returns_404(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx_a = _build_client(enforced_auth_settings, role=Role.admin())
    created = ctx_a["client"].post(
        "/api/v1/compliance-documents",
        headers=_headers(ctx_a["organization_id"], ctx_a["token"]),
        json=_create_payload(
            document_type_id=ctx_a["document_type"].id.value, code="CD-TENANT"
        ),
    )
    document_id = created.json()["id"]
    ctx_b = _build_client(enforced_auth_settings, role=Role.admin())
    headers_b = _headers(ctx_b["organization_id"], ctx_b["token"])
    assert (
        ctx_b["client"]
        .get(f"/api/v1/compliance-documents/{document_id}", headers=headers_b)
        .status_code
        == 404
    )
    patch_response = ctx_b["client"].patch(
        f"/api/v1/compliance-documents/{document_id}",
        headers=headers_b,
        json={"expected_version": 1, "title": "x"},
    )
    assert patch_response.status_code == 404
    # Cross-tenant document type in a create request is also masked as 404.
    cross_create = ctx_b["client"].post(
        "/api/v1/compliance-documents",
        headers=headers_b,
        json=_create_payload(
            document_type_id=ctx_a["document_type"].id.value, code="CD-TENANT-DT"
        ),
    )
    assert_error_envelope(
        cross_create, status_code=404, code="document_type_not_found"
    )


def test_auditor_cannot_create_or_update(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.auditor())
    headers = _headers(ctx["organization_id"], ctx["token"])
    response = ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(document_type_id=ctx["document_type"].id.value),
    )
    assert response.status_code == 403
    # Auditor can still read.
    list_response = ctx["client"].get(
        "/api/v1/compliance-documents", headers=headers
    )
    assert list_response.status_code == 200


def test_list_filters_and_pagination(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    for index in range(3):
        resp = ctx["client"].post(
            "/api/v1/compliance-documents",
            headers=headers,
            json=_create_payload(
                document_type_id=ctx["document_type"].id.value,
                code=f"CD-{index}",
                title=f"Title {index}",
            ),
        )
        assert resp.status_code == 201
    listed = ctx["client"].get(
        "/api/v1/compliance-documents",
        headers=headers,
        params={"status": "draft", "search": "Title", "limit": 2, "offset": 0},
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["pagination"]["total"] == 3
    assert len(body["items"]) == 2

    bad_status = ctx["client"].get(
        "/api/v1/compliance-documents", headers=headers, params={"status": "bogus"}
    )
    assert bad_status.status_code == 422


def test_list_review_due_filter_uses_backend_clock(
    enforced_auth_settings: AppSettings,
) -> None:
    """`is_review_due=true` keeps only documents in force past the warning window."""
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    now = datetime.now(UTC)
    due = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=ctx["document_type"],
        code="CD-DUE",
        title="Due soon",
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=now.date(),
        next_review_at=now.date(),
    ).model_copy(update={"status": ComplianceDocumentStatus.ACTIVE})
    far = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=ctx["document_type"],
        code="CD-FAR",
        title="Far away",
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=now.date(),
        next_review_at=now.date().replace(year=now.year + 5),
    ).model_copy(update={"status": ComplianceDocumentStatus.ACTIVE})
    ctx["compliance_documents"].add(due)
    ctx["compliance_documents"].add(far)
    headers = _headers(ctx["organization_id"], ctx["token"])
    response = ctx["client"].get(
        "/api/v1/compliance-documents",
        headers=headers,
        params={"review_due": "true"},
    )
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()["items"]}
    assert "CD-DUE" in codes
    assert "CD-FAR" not in codes


def test_list_filters_by_safety_domain(
    enforced_auth_settings: AppSettings,
) -> None:
    """`safety_domain` resolves to matching type ids in the handler."""
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    fire_type = DocumentType.create(
        organization_id=ctx["organization_id"],
        code="fire_regulation",
        title_ru="Пожарный регламент",
        safety_domain=SafetyDomain.FIRE,
        subject_kind=DocumentSubjectKind.ORGANIZATION,
        review_period_months=12,
        created_at=datetime.now(UTC),
    )
    ctx["document_types"].add(fire_type)
    headers = _headers(ctx["organization_id"], ctx["token"])
    ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(
            document_type_id=ctx["document_type"].id.value, code="CD-OCC"
        ),
    )
    ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(
            document_type_id=fire_type.id.value, code="CD-FIRE"
        ),
    )
    response = ctx["client"].get(
        "/api/v1/compliance-documents",
        headers=headers,
        params={"safety_domain": "fire"},
    )
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()["items"]}
    assert codes == {"CD-FIRE"}


def test_no_delete_route(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    created = ctx["client"].post(
        "/api/v1/compliance-documents",
        headers=headers,
        json=_create_payload(
            document_type_id=ctx["document_type"].id.value, code="CD-DEL"
        ),
    )
    document_id = created.json()["id"]
    schema = ctx["client"].get("/openapi.json").json()
    assert (
        "delete"
        not in schema["paths"]["/api/v1/compliance-documents/{document_id}"]
    )
    deleted = ctx["client"].delete(
        f"/api/v1/compliance-documents/{document_id}", headers=headers
    )
    assert deleted.status_code >= 400
    assert (
        ctx["client"]
        .get(f"/api/v1/compliance-documents/{document_id}", headers=headers)
        .status_code
        == 200
    )


def test_get_nonexistent_document_is_404(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    response = ctx["client"].get(
        f"/api/v1/compliance-documents/{uuid4()}", headers=headers
    )
    assert_error_envelope(
        response, status_code=404, code="compliance_document_not_found"
    )


def test_update_clearing_date_with_explicit_null(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    payload = _create_payload(
        document_type_id=ctx["document_type"].id.value, code="CD-CLR"
    )
    payload["effective_from"] = "2026-01-15"
    created = ctx["client"].post(
        "/api/v1/compliance-documents", headers=headers, json=payload
    )
    document_id = created.json()["id"]
    cleared = ctx["client"].patch(
        f"/api/v1/compliance-documents/{document_id}",
        headers=headers,
        json={"expected_version": 1, "effective_from": None},
    )
    assert cleared.status_code == 200
    assert cleared.json()["effective_from"] is None

    retained = ctx["client"].patch(
        f"/api/v1/compliance-documents/{document_id}",
        headers=headers,
        json={"expected_version": 2, "notes": "touch"},
    )
    assert retained.status_code == 200
    assert retained.json()["effective_from"] is None  # still cleared
    assert retained.json()["notes"] == "touch"


# Keep an unused import of ComplianceDocumentId / DocumentTypeId quiet.
_ = (ComplianceDocumentId, DocumentTypeId, ComplianceDocumentSource)
