from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.compliance_document_files import (
    ConfirmComplianceDocumentFileCommand,
    CreateComplianceDocumentUploadUrlCommand,
)
from backend.core.application.handlers.compliance_documents.get_list_compliance_documents import (
    ComplianceDocumentWithContext,
)
from backend.core.application.queries.compliance_documents import (
    GetComplianceDocumentQuery,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.storage import (
    PresignedUpload,
    StorageContract,
    StorageRequestRejectedError,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentFileNotFound,
    ComplianceDocumentFileTooLarge,
    ComplianceDocumentFileTypeNotAllowed,
    ComplianceDocumentNotFound,
    ComplianceDocumentValidationError,
    DocumentTypeNotFound,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentFile,
)
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/png",
        "image/jpeg",
    }
)

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_filename(filename: str) -> str:
    base = filename.strip().replace("\\", "/").split("/")[-1]
    if not base or base in {".", ".."}:
        return "file"
    safe = _SAFE_FILENAME.sub("_", base).strip("._")
    return safe or "file"


def _build_key(
    *,
    organization_id_value: str,
    document_id_value: str,
    upload_id_value: str,
    safe_filename: str,
) -> str:
    return (
        f"{organization_id_value}/compliance_document/"
        f"{document_id_value}/{upload_id_value}/{safe_filename}"
    )


def _validate_content_type(content_type: str) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ComplianceDocumentFileTypeNotAllowed(content_type)


def _validate_size(size_bytes: int, limit: int) -> None:
    if size_bytes > limit:
        raise ComplianceDocumentFileTooLarge(
            size_bytes=size_bytes, limit_bytes=limit
        )


@dataclass(frozen=True, slots=True)
class ComplianceDocumentUploadDescriptor:
    upload_id: str
    bucket: str
    key: str
    presigned: PresignedUpload


class CreateComplianceDocumentUploadUrlHandler:
    """Issue a presigned PUT for the direct upload of a draft document's file.

    The handler validates the request but writes nothing to persistent state;
    the file lands on the aggregate only after ``confirm``.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        storage: StorageContract,
        max_upload_bytes: int,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._storage = storage
        self._max_upload_bytes = max_upload_bytes

    def handle(
        self, command: CreateComplianceDocumentUploadUrlCommand
    ) -> ComplianceDocumentUploadDescriptor:
        document = self._unit_of_work.compliance_documents.get(
            command.organization_id, command.document_id
        )
        if document is None:
            raise ComplianceDocumentNotFound(command.document_id)
        if document.status is not ComplianceDocumentStatus.DRAFT:
            raise ComplianceDocumentValidationError(
                "Files can be uploaded only for draft documents."
            )
        _validate_content_type(command.content_type)
        _validate_size(command.size_bytes, self._max_upload_bytes)
        upload_id = str(uuid4())
        safe = _sanitize_filename(command.filename)
        key = _build_key(
            organization_id_value=str(command.organization_id.value),
            document_id_value=str(command.document_id.value),
            upload_id_value=upload_id,
            safe_filename=safe,
        )
        try:
            presigned = self._storage.create_upload_url(
                key=key,
                content_type=command.content_type,
                size_bytes=command.size_bytes,
                sha256=command.sha256,
            )
        except StorageRequestRejectedError as error:
            raise ComplianceDocumentValidationError(str(error)) from error
        return ComplianceDocumentUploadDescriptor(
            upload_id=upload_id,
            bucket=presigned.bucket,
            key=presigned.key,
            presigned=presigned,
        )


class ConfirmComplianceDocumentFileHandler:
    """Attach an uploaded object as the current file of a draft document."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        storage: StorageContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._storage = storage
        self._clock = clock
        self._audit = audit

    def handle(
        self, command: ConfirmComplianceDocumentFileCommand
    ) -> ComplianceDocumentWithContext:
        context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_DOCUMENT_FILE_ATTACHED,
            context=context,
            resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
            resource_id=command.document_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> tuple[ComplianceDocument, DocumentType]:
            document = self._unit_of_work.compliance_documents.get(
                command.organization_id, command.document_id
            )
            if document is None:
                raise ComplianceDocumentNotFound(command.document_id)
            if document.status is not ComplianceDocumentStatus.DRAFT:
                raise ComplianceDocumentValidationError(
                    "Files can be confirmed only for draft documents."
                )
            document_type = self._unit_of_work.document_types.get(
                document.organization_id, document.document_type_id
            )
            if document_type is None:
                raise DocumentTypeNotFound(document.document_type_id)
            # Never trust the client-supplied bucket; a confirm against another
            # bucket must be refused up front rather than relying on the storage
            # adapter's own owned-bucket guard.
            owned_bucket = self._storage.bucket
            if command.bucket != owned_bucket:
                raise ComplianceDocumentValidationError(
                    "Object bucket does not belong to this application."
                )
            if command.content_type not in ALLOWED_CONTENT_TYPES:
                raise ComplianceDocumentFileTypeNotAllowed(command.content_type)
            key_prefix = (
                f"{command.organization_id.value}/compliance_document/"
                f"{command.document_id.value}/"
            )
            if not command.key.startswith(key_prefix):
                raise ComplianceDocumentValidationError(
                    "Object key does not belong to this document."
                )
            info = self._storage.head(owned_bucket, command.key)
            if info is None:
                raise ComplianceDocumentValidationError(
                    "The uploaded object was not found in storage."
                )
            if info.size_bytes != command.size_bytes:
                raise ComplianceDocumentValidationError(
                    "The stored object size does not match the confirmation."
                )
            if info.content_type is not None and info.content_type != command.content_type:
                raise ComplianceDocumentValidationError(
                    "The stored object content type does not match the confirmation."
                )
            # D20: sha256 metadata is client-asserted; a missing value is an
            # accepted risk, but a mismatching one is rejected.
            if info.sha256 is not None and info.sha256.lower() != command.sha256.lower():
                raise ComplianceDocumentValidationError(
                    "The stored object SHA-256 does not match the confirmation."
                )
            file = DocumentFile(
                bucket=owned_bucket,
                key=command.key,
                size_bytes=command.size_bytes,
                content_type=command.content_type,
                sha256=command.sha256,
                original_filename=command.original_filename,
                uploaded_at=self._clock.now(),
                uploaded_by=command.actor_id,
            )
            attached = document.attach_file(
                file=file,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            return attached, document_type

        def success_spec(
            result: tuple[ComplianceDocument, DocumentType],
        ) -> AuditRecordSpec:
            attached, _document_type = result
            self._unit_of_work.compliance_documents.save(
                attached, expected_version=attached.version - 1
            )
            current = attached.current_file
            assert current is not None
            return AuditRecordSpec(
                action=AuditAction.COMPLIANCE_DOCUMENT_FILE_ATTACHED,
                context=context,
                resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                resource_id=attached.id.value,
                target_organization_id=attached.organization_id,
                metadata={
                    "document_id": str(attached.id.value),
                    "document_code": attached.code,
                    "file_id": str(current.id.value),
                    "file_size_bytes": str(current.size_bytes),
                    "file_sha256": current.sha256,
                    "resulting_version": str(attached.version),
                },
            )

        result = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        attached, document_type = result
        today = self._clock.now().date()
        return ComplianceDocumentWithContext(
            document=attached,
            document_type=document_type,
            is_review_due=attached.is_review_due(
                as_of=today, document_type=document_type
            ),
        )


@dataclass(frozen=True, slots=True)
class ComplianceDocumentDownloadDescriptor:
    url: str
    expires_at: object
    file: DocumentFile


class GetComplianceDocumentDownloadUrlHandler:
    """Sign a GET for the current file of a document (any status)."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        storage: StorageContract,
        clock: ClockContract,
        presign_ttl_seconds: int,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._storage = storage
        self._clock = clock
        self._presign_ttl_seconds = presign_ttl_seconds

    def handle(
        self, query: GetComplianceDocumentQuery
    ) -> ComplianceDocumentDownloadDescriptor:
        document = self._unit_of_work.compliance_documents.get(
            query.organization_id, query.document_id
        )
        if document is None:
            raise ComplianceDocumentNotFound(query.document_id)
        current = document.current_file
        if current is None:
            raise ComplianceDocumentFileNotFound(document.id)
        ttl = timedelta(seconds=self._presign_ttl_seconds)
        try:
            url = self._storage.create_download_url(
                bucket=current.bucket,
                key=current.key,
                ttl=ttl,
                filename=current.original_filename,
                content_type=current.content_type,
            )
        except StorageRequestRejectedError as error:
            raise ComplianceDocumentValidationError(str(error)) from error
        return ComplianceDocumentDownloadDescriptor(
            url=url,
            expires_at=self._clock.now() + ttl,
            file=current,
        )


class ListComplianceDocumentFilesHandler:
    """Return every file ever attached to a document, oldest first."""

    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(
        self, query: GetComplianceDocumentQuery
    ) -> tuple[DocumentFile, ...]:
        document = self._unit_of_work.compliance_documents.get(
            query.organization_id, query.document_id
        )
        if document is None:
            raise ComplianceDocumentNotFound(query.document_id)
        return document.files
