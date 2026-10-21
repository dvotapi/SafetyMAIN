from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.compliance_documents import (
    CreateComplianceDocumentCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentValidationError,
    DocumentTypeNotFound,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class CreateComplianceDocumentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: CreateComplianceDocumentCommand) -> ComplianceDocument:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_DOCUMENT_CREATED,
            context=audit_context,
            resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
            target_organization_id=command.organization_id,
            metadata={"document_code": command.code},
        )

        def operation() -> ComplianceDocument:
            document_type = self._unit_of_work.document_types.get(
                command.organization_id,
                command.document_type_id,
            )
            if document_type is None:
                raise DocumentTypeNotFound(command.document_type_id)
            # Soft existence checks for related documents in the same organization.
            # Full type/status checks for ``supersedes`` and ``approved_by`` move
            # to the lifecycle handlers in Phase 5.
            if (
                command.approved_by_document_id is not None
                and self._unit_of_work.compliance_documents.get(
                    command.organization_id,
                    command.approved_by_document_id,
                )
                is None
            ):
                raise ComplianceDocumentValidationError(
                    "The approval order document does not exist."
                )
            if (
                command.supersedes_document_id is not None
                and self._unit_of_work.compliance_documents.get(
                    command.organization_id,
                    command.supersedes_document_id,
                )
                is None
            ):
                raise ComplianceDocumentValidationError(
                    "The superseded document does not exist."
                )
            now = self._clock.now()
            return ComplianceDocument.create(
                organization_id=command.organization_id,
                document_type=document_type,
                code=command.code,
                title=command.title,
                created_by=command.actor_id,
                created_at=now,
                subject_id=command.subject_id,
                issued_at=command.issued_at,
                effective_from=command.effective_from,
                next_review_at=command.next_review_at,
                approved_by_document_id=command.approved_by_document_id,
                supersedes_document_id=command.supersedes_document_id,
                applicability=command.applicability,
                source=command.source,
                notes=command.notes,
            )

        def success_spec(document: ComplianceDocument) -> AuditRecordSpec:
            self._unit_of_work.compliance_documents.add(document)
            return AuditRecordSpec(
                action=AuditAction.COMPLIANCE_DOCUMENT_CREATED,
                context=audit_context,
                resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                resource_id=document.id.value,
                target_organization_id=document.organization_id,
                metadata={
                    "document_id": str(document.id.value),
                    "document_code": document.code,
                    "document_type_id": str(document.document_type_id.value),
                    "subject_kind": document.subject_kind.value,
                    "new_status": document.status.value,
                },
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
