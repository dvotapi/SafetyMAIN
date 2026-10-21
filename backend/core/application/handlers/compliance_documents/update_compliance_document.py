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
    UNSET,
    UpdateComplianceDocumentCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentNotFound,
    ComplianceDocumentValidationError,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def _unwrap(value: object) -> object:
    """Map command sentinel to the domain's ``...`` sentinel."""
    return ... if value is UNSET else value


class UpdateComplianceDocumentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: UpdateComplianceDocumentCommand) -> ComplianceDocument:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_DOCUMENT_UPDATED,
            context=audit_context,
            resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
            resource_id=command.document_id.value,
            target_organization_id=command.organization_id,
            metadata={"document_id": str(command.document_id.value)},
        )

        def operation() -> ComplianceDocument:
            existing = self._unit_of_work.compliance_documents.get(
                command.organization_id,
                command.document_id,
            )
            if existing is None:
                raise ComplianceDocumentNotFound(command.document_id)
            if (
                command.approved_by_document_id is not UNSET
                and command.approved_by_document_id is not None
                and self._unit_of_work.compliance_documents.get(
                    command.organization_id,
                    command.approved_by_document_id,  # type: ignore[arg-type]
                )
                is None
            ):
                raise ComplianceDocumentValidationError(
                    "The approval order document does not exist."
                )
            if (
                command.supersedes_document_id is not UNSET
                and command.supersedes_document_id is not None
                and self._unit_of_work.compliance_documents.get(
                    command.organization_id,
                    command.supersedes_document_id,  # type: ignore[arg-type]
                )
                is None
            ):
                raise ComplianceDocumentValidationError(
                    "The superseded document does not exist."
                )
            updated = existing.update_details(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                code=command.code,
                title=command.title,
                issued_at=_unwrap(command.issued_at),
                effective_from=_unwrap(command.effective_from),
                next_review_at=_unwrap(command.next_review_at),
                approved_by_document_id=_unwrap(command.approved_by_document_id),
                supersedes_document_id=_unwrap(command.supersedes_document_id),
                applicability=command.applicability,
                notes=command.notes,
            )
            self._unit_of_work.compliance_documents.save(
                updated, expected_version=command.expected_version
            )
            return updated

        def success_spec(document: ComplianceDocument) -> AuditRecordSpec:
            return AuditRecordSpec(
                action=AuditAction.COMPLIANCE_DOCUMENT_UPDATED,
                context=audit_context,
                resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                resource_id=document.id.value,
                target_organization_id=document.organization_id,
                metadata={
                    "document_id": str(document.id.value),
                    "document_code": document.code,
                    "new_version": document.version,
                },
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )

