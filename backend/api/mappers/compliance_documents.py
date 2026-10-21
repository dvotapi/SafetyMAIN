from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.api.schemas.compliance_documents import (
    ComplianceDocumentListResponse,
    ComplianceDocumentResponse,
    DocumentApplicabilityPayload,
    DocumentFileResponse,
    DocumentTypeListResponse,
    DocumentTypeResponse,
    UpdateComplianceDocumentRequest,
)
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.application.commands.compliance_documents import UNSET
from backend.core.application.handlers.compliance_documents.get_list_compliance_documents import (
    ComplianceDocumentPageWithContext,
    ComplianceDocumentWithContext,
)
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentValidationError,
)
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentApplicability,
    DocumentFile,
)


def to_applicability_payload(
    applicability: DocumentApplicability,
) -> DocumentApplicabilityPayload:
    return DocumentApplicabilityPayload(
        positions=list(applicability.positions),
        work_types=list(applicability.work_types),
        departments=list(applicability.departments),
        asset_ids=list(applicability.asset_ids),
    )


def from_applicability_payload(
    payload: DocumentApplicabilityPayload | None,
) -> DocumentApplicability | None:
    if payload is None:
        return None
    try:
        return DocumentApplicability(
            positions=tuple(payload.positions),
            work_types=tuple(payload.work_types),
            departments=tuple(payload.departments),
            asset_ids=tuple(payload.asset_ids),
        )
    except ValidationError as error:
        detail = error.errors()[0]
        message = detail.get("ctx", {}).get("error") or detail["msg"]
        raise ComplianceDocumentValidationError(str(message)) from error


def to_file_response(file: DocumentFile) -> DocumentFileResponse:
    return DocumentFileResponse(
        id=file.id.value,
        bucket=file.bucket,
        key=file.key,
        size_bytes=file.size_bytes,
        content_type=file.content_type,
        sha256=file.sha256,
        original_filename=file.original_filename,
        uploaded_at=file.uploaded_at,
        uploaded_by=file.uploaded_by.value,
    )


def to_document_type_response(document_type: DocumentType) -> DocumentTypeResponse:
    return DocumentTypeResponse(
        id=document_type.id.value,
        organization_id=document_type.organization_id.value,
        code=document_type.code,
        title_ru=document_type.title_ru,
        safety_domain=document_type.safety_domain.value,  # type: ignore[arg-type]
        subject_kind=document_type.subject_kind.value,  # type: ignore[arg-type]
        review_period_months=document_type.review_period_months,
        validity_months=document_type.validity_months,
        periodicity_months=document_type.periodicity_months,
        warning_thresholds_days=list(document_type.warning_thresholds_days),
        requires_acknowledgement=document_type.requires_acknowledgement,
        requires_approval_order=document_type.requires_approval_order,
        legal_basis=document_type.legal_basis,
        legal_basis_reference=document_type.legal_basis_reference,
        is_active=document_type.is_active,
        created_at=document_type.created_at,
        updated_at=document_type.updated_at,
    )


def to_document_type_list_response(
    document_types: tuple[DocumentType, ...],
) -> DocumentTypeListResponse:
    return DocumentTypeListResponse(
        items=[to_document_type_response(item) for item in document_types]
    )


def to_compliance_document_response(
    document: ComplianceDocument,
    *,
    is_review_due: bool,
) -> ComplianceDocumentResponse:
    return ComplianceDocumentResponse(
        id=document.id.value,
        organization_id=document.organization_id.value,
        document_type_id=document.document_type_id.value,
        subject_kind=document.subject_kind.value,  # type: ignore[arg-type]
        subject_id=document.subject_id,
        code=document.code,
        title=document.title,
        status=document.status.value,  # type: ignore[arg-type]
        issued_at=document.issued_at,
        effective_from=document.effective_from,
        next_review_at=document.next_review_at,
        approved_by_document_id=(
            None
            if document.approved_by_document_id is None
            else document.approved_by_document_id.value
        ),
        supersedes_document_id=(
            None
            if document.supersedes_document_id is None
            else document.supersedes_document_id.value
        ),
        superseded_by_document_id=(
            None
            if document.superseded_by_document_id is None
            else document.superseded_by_document_id.value
        ),
        applicability=to_applicability_payload(document.applicability),
        source=document.source.value,  # type: ignore[arg-type]
        current_file=(
            None if document.current_file is None else to_file_response(document.current_file)
        ),
        notes=document.notes,
        status_before_archive=(
            None
            if document.status_before_archive is None
            else document.status_before_archive.value  # type: ignore[arg-type]
        ),
        archive_reason=document.archive_reason,
        is_review_due=is_review_due,
        created_at=document.created_at,
        created_by=document.created_by.value,
        updated_at=document.updated_at,
        updated_by=document.updated_by.value,
        version=document.version,
    )


def to_compliance_document_response_from_context(
    item: ComplianceDocumentWithContext,
) -> ComplianceDocumentResponse:
    return to_compliance_document_response(
        item.document, is_review_due=item.is_review_due
    )


def to_compliance_document_list_response(
    page: ComplianceDocumentPageWithContext,
) -> ComplianceDocumentListResponse:
    return ComplianceDocumentListResponse(
        items=[to_compliance_document_response_from_context(item) for item in page.items],
        pagination=PaginationResponse(
            offset=page.offset, limit=page.limit, total=page.total
        ),
    )


def update_fields_from_request(
    request_body: UpdateComplianceDocumentRequest,
) -> dict[str, Any]:
    """Translate the update DTO into kwargs for the handler command.

    The sentinel ``UNSET`` carries "field omitted" through to the domain, so
    the mapper reads ``model_fields_set`` to distinguish absent values from
    an explicit ``null`` on nullable fields.
    """
    set_fields = request_body.model_fields_set
    nullable_fields = (
        "issued_at",
        "effective_from",
        "next_review_at",
        "approved_by_document_id",
        "supersedes_document_id",
    )
    kwargs: dict[str, Any] = {}
    for name in nullable_fields:
        kwargs[name] = (
            getattr(request_body, name) if name in set_fields else UNSET
        )
    return kwargs
