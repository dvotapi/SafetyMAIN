from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentApplicability,
    DocumentFile,
)
from backend.core.domain.value_objects.compliance_enums import (
    DocumentSubjectKind,
    SafetyDomain,
)

FIXED_AT = datetime(2026, 10, 1, 9, 30, tzinfo=UTC)
SHA256_HEX = "a" * 64


def make_actor() -> UserId:
    return UserId(value=uuid4())


def make_document_type(
    *,
    organization_id: OrganizationId | None = None,
    code: str = "iot_profession",
    title_ru: str = "Инструкция по охране труда для профессии",
    safety_domain: SafetyDomain = SafetyDomain.OCCUPATIONAL,
    subject_kind: DocumentSubjectKind = DocumentSubjectKind.ORGANIZATION,
    review_period_months: int | None = 60,
    validity_months: int | None = None,
    periodicity_months: int | None = None,
    warning_thresholds_days: tuple[int, ...] = (90, 30, 14, 7),
    requires_approval_order: bool = False,
    is_active: bool = True,
    created_at: datetime = FIXED_AT,
) -> DocumentType:
    return DocumentType.create(
        organization_id=organization_id or OrganizationId(value=uuid4()),
        code=code,
        title_ru=title_ru,
        safety_domain=safety_domain,
        subject_kind=subject_kind,
        review_period_months=review_period_months,
        validity_months=validity_months,
        periodicity_months=periodicity_months,
        warning_thresholds_days=warning_thresholds_days,
        requires_approval_order=requires_approval_order,
        is_active=is_active,
        created_at=created_at,
    )


def make_document_file(
    document: ComplianceDocument,
    *,
    uploaded_by: UserId | None = None,
    uploaded_at: datetime = FIXED_AT,
    filename: str = "iot-012.pdf",
) -> DocumentFile:
    upload_id = uuid4()
    return DocumentFile(
        bucket="safetymain-documents",
        key=(
            f"{document.organization_id.value}/compliance_document/"
            f"{document.id.value}/{upload_id}/{filename}"
        ),
        size_bytes=2048,
        content_type="application/pdf",
        sha256=SHA256_HEX,
        original_filename=filename,
        uploaded_at=uploaded_at,
        uploaded_by=uploaded_by or document.created_by,
    )


def compliance_document_draft(
    document_type: DocumentType | None = None,
    *,
    organization_id: OrganizationId | None = None,
    code: str = "ИОТ-012",
    title: str = "Инструкция по охране труда для водителя",
    created_by: UserId | None = None,
    created_at: datetime = FIXED_AT,
    effective_from: date | None = date(2026, 10, 1),
    **kwargs: object,
) -> ComplianceDocument:
    document_type = document_type or make_document_type(organization_id=organization_id)
    return ComplianceDocument.create(
        organization_id=document_type.organization_id,
        document_type=document_type,
        code=code,
        title=title,
        created_by=created_by or make_actor(),
        created_at=created_at,
        effective_from=effective_from,
        **kwargs,
    )


def with_file(document: ComplianceDocument, *, at: datetime = FIXED_AT) -> ComplianceDocument:
    return document.attach_file(
        file=make_document_file(document, uploaded_at=at),
        at=at,
        actor_id=document.created_by,
        expected_version=document.version,
    )


def advance_to_approved(
    document: ComplianceDocument, *, at: datetime = FIXED_AT
) -> ComplianceDocument:
    attached = with_file(document, at=at)
    return attached.approve(
        at=at, actor_id=document.created_by, expected_version=attached.version
    )


def advance_to_active(
    document: ComplianceDocument,
    document_type: DocumentType,
    *,
    at: datetime = FIXED_AT,
) -> ComplianceDocument:
    approved = advance_to_approved(document, at=at)
    return approved.activate(
        document_type=document_type,
        at=at,
        actor_id=document.created_by,
        expected_version=approved.version,
    )


def rich_applicability() -> DocumentApplicability:
    return DocumentApplicability(
        positions=("Водитель", "Механик"),
        work_types=("Работа на высоте",),
        departments=("Автоколонна 1",),
        asset_ids=(uuid4(),),
    )
