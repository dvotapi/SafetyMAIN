from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.membership import Membership
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, Role
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentFile,
)
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentStatus,
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
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


def _file(*, uploaded_by: Any, bucket: str = "test-bucket") -> DocumentFile:
    return DocumentFile(
        bucket=bucket,
        key="org/compliance_document/doc/upload/file.pdf",
        size_bytes=1024,
        content_type="application/pdf",
        sha256="a" * 64,
        original_filename="file.pdf",
        uploaded_at=datetime.now(UTC),
        uploaded_by=uploaded_by,
    )


def _seed_draft_with_file(ctx: dict[str, Any], **overrides: Any) -> ComplianceDocument:
    """Seed a draft document with a current file ready for approval."""
    now = datetime.now(UTC)
    document = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=ctx["document_type"],
        code=overrides.pop("code", f"CD-{uuid4().hex[:6]}"),
        title=overrides.pop("title", "Act"),
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=overrides.pop("effective_from", now.date()),
        **overrides,
    )
    document = document.attach_file(
        file=_file(uploaded_by=ctx["user_id"]),
        at=now,
        actor_id=ctx["user_id"],
        expected_version=1,
    )
    ctx["compliance_documents"].add(document)
    return document


def _approve_api(
    client: Any, headers: dict[str, str], document_id: Any, version: int
) -> Any:
    return client.post(
        f"/api/v1/compliance-documents/{document_id}/approve",
        headers=headers,
        json={"expected_version": version},
    )


def _activate_api(
    client: Any, headers: dict[str, str], document_id: Any, version: int
) -> Any:
    return client.post(
        f"/api/v1/compliance-documents/{document_id}/activate",
        headers=headers,
        json={"expected_version": version},
    )


def test_full_lifecycle_draft_to_superseded(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])

    first = _seed_draft_with_file(ctx, code="CD-01")

    approved = _approve_api(ctx["client"], headers, first.id.value, 2)
    assert approved.status_code == 200, approved.json()
    assert approved.json()["status"] == "approved"
    assert approved.json()["version"] == 3

    activated = _activate_api(ctx["client"], headers, first.id.value, 3)
    assert activated.status_code == 200, activated.json()
    assert activated.json()["status"] == "active"
    assert activated.json()["next_review_at"] is not None

    started = ctx["client"].post(
        f"/api/v1/compliance-documents/{first.id.value}/start-review",
        headers=headers,
        json={"expected_version": 4},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "under_review"

    completed = ctx["client"].post(
        f"/api/v1/compliance-documents/{first.id.value}/complete-review",
        headers=headers,
        json={"expected_version": 5, "completed_on": "2026-11-01"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "active"

    # Second edition supersedes the first atomically on activation.
    second = _seed_draft_with_file(
        ctx,
        code="CD-02",
        supersedes_document_id=first.id,
    )
    _approve_api(ctx["client"], headers, second.id.value, 2)
    activate_second = _activate_api(ctx["client"], headers, second.id.value, 3)
    assert activate_second.status_code == 200, activate_second.json()
    assert activate_second.json()["status"] == "active"

    old = ctx["client"].get(
        f"/api/v1/compliance-documents/{first.id.value}", headers=headers
    )
    assert old.status_code == 200
    assert old.json()["status"] == "superseded"
    assert old.json()["superseded_by_document_id"] == str(second.id.value)

    actions = [
        event.action.value for event in ctx["audit_events"].snapshot().values()
    ]
    assert "compliance.document.approved" in actions
    assert "compliance.document.activated" in actions
    assert "compliance.document.review_started" in actions
    assert "compliance.document.review_completed" in actions
    assert "compliance.document.superseded" in actions


def test_archive_and_restore_from_draft(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    document = _seed_draft_with_file(ctx)
    archived = ctx["client"].post(
        f"/api/v1/compliance-documents/{document.id.value}/archive",
        headers=headers,
        json={"expected_version": 2, "reason": "obsolete"},
    )
    assert archived.status_code == 200, archived.json()
    assert archived.json()["status"] == "archived"
    assert archived.json()["status_before_archive"] == "draft"

    restored = ctx["client"].post(
        f"/api/v1/compliance-documents/{document.id.value}/restore",
        headers=headers,
        json={"expected_version": 3, "reason": "needed again"},
    )
    assert restored.status_code == 200, restored.json()
    assert restored.json()["status"] == "draft"
    assert restored.json()["status_before_archive"] is None


def test_activate_requires_approval_order_when_type_requires_it(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    # Seed order type and a non-order approving document path.
    order_type = _seed_type(
        ctx["organization_id"], code="order", requires_approval_order=False
    )
    ctx["document_types"].add(order_type)
    non_order_type = _seed_type(
        ctx["organization_id"], code="not_an_order", requires_approval_order=False
    )
    ctx["document_types"].add(non_order_type)
    # The main doc's type requires approval order.
    main_type = _seed_type(
        ctx["organization_id"],
        code="iot_profession_order_required",
        requires_approval_order=True,
    )
    ctx["document_types"].add(main_type)
    now = datetime.now(UTC)

    # Approving order document (active, type == "order").
    order_doc = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=order_type,
        code="ORDER-1",
        title="Approval order",
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=now.date(),
    )
    order_doc = order_doc.attach_file(
        file=_file(uploaded_by=ctx["user_id"]),
        at=now,
        actor_id=ctx["user_id"],
        expected_version=1,
    ).model_copy(update={"status": ComplianceDocumentStatus.ACTIVE})
    ctx["compliance_documents"].add(order_doc)

    # Main document whose type requires an approving order.
    main = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=main_type,
        code="MAIN-1",
        title="Local act",
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=now.date(),
        approved_by_document_id=order_doc.id,
    )
    main = main.attach_file(
        file=_file(uploaded_by=ctx["user_id"]),
        at=now,
        actor_id=ctx["user_id"],
        expected_version=1,
    ).model_copy(update={"status": ComplianceDocumentStatus.APPROVED, "version": 3})
    ctx["compliance_documents"].add(main)
    headers = _headers(ctx["organization_id"], ctx["token"])

    ok = _activate_api(ctx["client"], headers, main.id.value, 3)
    assert ok.status_code == 200, ok.json()

    # Now point to a non-order approving document and attempt activation.
    bad_approver = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=non_order_type,
        code="BAD-APPROVER",
        title="Something else",
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=now.date(),
    )
    bad_approver = bad_approver.attach_file(
        file=_file(uploaded_by=ctx["user_id"]),
        at=now,
        actor_id=ctx["user_id"],
        expected_version=1,
    ).model_copy(update={"status": ComplianceDocumentStatus.ACTIVE})
    ctx["compliance_documents"].add(bad_approver)

    bad_main = ComplianceDocument.create(
        organization_id=ctx["organization_id"],
        document_type=main_type,
        code="MAIN-2",
        title="Another local act",
        created_by=ctx["user_id"],
        created_at=now,
        effective_from=now.date(),
        approved_by_document_id=bad_approver.id,
    )
    bad_main = bad_main.attach_file(
        file=_file(uploaded_by=ctx["user_id"]),
        at=now,
        actor_id=ctx["user_id"],
        expected_version=1,
    ).model_copy(update={"status": ComplianceDocumentStatus.APPROVED, "version": 3})
    ctx["compliance_documents"].add(bad_main)

    bad = _activate_api(ctx["client"], headers, bad_main.id.value, 3)
    assert_error_envelope(
        bad, status_code=422, code="compliance_document_validation_error"
    )


def test_version_conflict_on_approve(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    document = _seed_draft_with_file(ctx)
    stale = _approve_api(ctx["client"], headers, document.id.value, 1)
    assert_error_envelope(
        stale, status_code=409, code="compliance_document_version_conflict"
    )


def test_invalid_transition_on_activate_from_draft(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    document = _seed_draft_with_file(ctx)
    bad = _activate_api(ctx["client"], headers, document.id.value, 2)
    assert_error_envelope(
        bad, status_code=422, code="invalid_compliance_document_transition"
    )


def test_cross_tenant_lifecycle_returns_404(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx_a = _build_client(enforced_auth_settings, role=Role.admin())
    document = _seed_draft_with_file(ctx_a)
    ctx_b = _build_client(enforced_auth_settings, role=Role.admin())
    headers_b = _headers(ctx_b["organization_id"], ctx_b["token"])
    response = _approve_api(ctx_b["client"], headers_b, document.id.value, 2)
    assert_error_envelope(
        response, status_code=404, code="compliance_document_not_found"
    )


def test_role_matrix_lifecycle_permissions(
    enforced_auth_settings: AppSettings,
) -> None:
    # Member cannot approve, activate, archive, or restore.
    for role in (Role.member(), Role.auditor()):
        ctx = _build_client(enforced_auth_settings, role=role)
        headers = _headers(ctx["organization_id"], ctx["token"])
        document = _seed_draft_with_file(ctx)
        assert _approve_api(
            ctx["client"], headers, document.id.value, 2
        ).status_code == 403
        assert ctx["client"].post(
            f"/api/v1/compliance-documents/{document.id.value}/archive",
            headers=headers,
            json={"expected_version": 2, "reason": "no"},
        ).status_code == 403

    # Auditor cannot start-review either.
    auditor_ctx = _build_client(enforced_auth_settings, role=Role.auditor())
    headers = _headers(auditor_ctx["organization_id"], auditor_ctx["token"])
    document = _seed_draft_with_file(auditor_ctx)
    assert auditor_ctx["client"].post(
        f"/api/v1/compliance-documents/{document.id.value}/start-review",
        headers=headers,
        json={"expected_version": 2},
    ).status_code == 403


def test_restore_only_from_archived(enforced_auth_settings: AppSettings) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    document = _seed_draft_with_file(ctx)
    bad = ctx["client"].post(
        f"/api/v1/compliance-documents/{document.id.value}/restore",
        headers=headers,
        json={"expected_version": 2, "reason": "x"},
    )
    assert_error_envelope(
        bad, status_code=422, code="invalid_compliance_document_transition"
    )


def test_approve_on_unknown_document_returns_404(
    enforced_auth_settings: AppSettings,
) -> None:
    ctx = _build_client(enforced_auth_settings, role=Role.admin())
    headers = _headers(ctx["organization_id"], ctx["token"])
    unknown_id = ComplianceDocumentId(value=uuid4())
    response = _approve_api(ctx["client"], headers, unknown_id.value, 1)
    assert_error_envelope(
        response, status_code=404, code="compliance_document_not_found"
    )
