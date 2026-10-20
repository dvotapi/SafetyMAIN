from __future__ import annotations

from collections.abc import Sequence

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentApplicability,
    DocumentFile,
)
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentSource,
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentFileId,
    DocumentTypeId,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.compliance_document_model import (
    ComplianceDocumentModel,
    DocumentFileModel,
)


def to_model(document: ComplianceDocument) -> ComplianceDocumentModel:
    return ComplianceDocumentModel(
        id=document.id.value,
        organization_id=document.organization_id.value,
        document_type_id=document.document_type_id.value,
        subject_kind=document.subject_kind.value,
        subject_id=document.subject_id,
        code=document.code,
        title=document.title,
        status=document.status.value,
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
        applicability=document.applicability.model_dump(mode="json"),
        source=document.source.value,
        notes=document.notes,
        status_before_archive=(
            None
            if document.status_before_archive is None
            else document.status_before_archive.value
        ),
        archive_reason=document.archive_reason,
        created_at=document.created_at,
        created_by=document.created_by.value,
        updated_at=document.updated_at,
        updated_by=document.updated_by.value,
        version=document.version,
    )


def files_to_models(document: ComplianceDocument) -> list[DocumentFileModel]:
    return [
        DocumentFileModel(
            id=file.id.value,
            document_id=document.id.value,
            position=index,
            bucket=file.bucket,
            key=file.key,
            size_bytes=file.size_bytes,
            content_type=file.content_type,
            sha256=file.sha256,
            original_filename=file.original_filename,
            uploaded_at=file.uploaded_at,
            uploaded_by=file.uploaded_by.value,
        )
        for index, file in enumerate(document.files)
    ]


def file_to_domain(model: DocumentFileModel) -> DocumentFile:
    return DocumentFile(
        id=DocumentFileId(value=model.id),
        bucket=model.bucket,
        key=model.key,
        size_bytes=model.size_bytes,
        content_type=model.content_type,
        sha256=model.sha256,
        original_filename=model.original_filename,
        uploaded_at=model.uploaded_at,
        uploaded_by=UserId(value=model.uploaded_by),
    )


def to_domain(
    model: ComplianceDocumentModel, files: Sequence[DocumentFileModel]
) -> ComplianceDocument:
    """Build a ComplianceDocument from a row and its files already ordered by position."""
    return ComplianceDocument(
        id=ComplianceDocumentId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        document_type_id=DocumentTypeId(value=model.document_type_id),
        subject_kind=DocumentSubjectKind(model.subject_kind),
        subject_id=model.subject_id,
        code=model.code,
        title=model.title,
        status=ComplianceDocumentStatus(model.status),
        issued_at=model.issued_at,
        effective_from=model.effective_from,
        next_review_at=model.next_review_at,
        approved_by_document_id=(
            None
            if model.approved_by_document_id is None
            else ComplianceDocumentId(value=model.approved_by_document_id)
        ),
        supersedes_document_id=(
            None
            if model.supersedes_document_id is None
            else ComplianceDocumentId(value=model.supersedes_document_id)
        ),
        superseded_by_document_id=(
            None
            if model.superseded_by_document_id is None
            else ComplianceDocumentId(value=model.superseded_by_document_id)
        ),
        applicability=DocumentApplicability.model_validate(model.applicability or {}),
        source=ComplianceDocumentSource(model.source),
        files=tuple(file_to_domain(file) for file in files),
        notes=model.notes,
        status_before_archive=(
            None
            if model.status_before_archive is None
            else ComplianceDocumentStatus(model.status_before_archive)
        ),
        archive_reason=model.archive_reason,
        created_at=model.created_at,
        created_by=UserId(value=model.created_by),
        updated_at=model.updated_at,
        updated_by=UserId(value=model.updated_by),
        version=model.version,
    )
