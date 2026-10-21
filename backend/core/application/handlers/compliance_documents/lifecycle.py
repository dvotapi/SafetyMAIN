from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.compliance_document_lifecycle import (
    ActivateComplianceDocumentCommand,
    ApproveComplianceDocumentCommand,
    ArchiveComplianceDocumentCommand,
    CompleteReviewComplianceDocumentCommand,
    RestoreComplianceDocumentCommand,
    StartReviewComplianceDocumentCommand,
)
from backend.core.application.handlers.compliance_documents.get_list_compliance_documents import (
    ComplianceDocumentWithContext,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentNotFound,
    ComplianceDocumentValidationError,
    DocumentTypeNotFound,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus

APPROVAL_ORDER_TYPE_CODE = "order"
"""Type code of a document that approves other documents (D1-D20, §Lifecycle)."""


def _load(
    unit_of_work: UnitOfWorkContract,
    *,
    organization_id: Any,
    document_id: Any,
) -> ComplianceDocument:
    document = unit_of_work.compliance_documents.get(organization_id, document_id)
    if document is None:
        raise ComplianceDocumentNotFound(document_id)
    return document


def _load_type(
    unit_of_work: UnitOfWorkContract,
    *,
    organization_id: Any,
    document_type_id: Any,
) -> DocumentType:
    document_type = unit_of_work.document_types.get(organization_id, document_type_id)
    if document_type is None:
        raise DocumentTypeNotFound(document_type_id)
    return document_type


def _review_due_context(
    document: ComplianceDocument,
    document_type: DocumentType,
    clock: ClockContract,
) -> ComplianceDocumentWithContext:
    today = clock.now().date()
    return ComplianceDocumentWithContext(
        document=document,
        document_type=document_type,
        is_review_due=document.is_review_due(as_of=today, document_type=document_type),
    )


def _meta(document: ComplianceDocument, *, previous_status: str) -> dict[str, str]:
    return {
        "document_id": str(document.id.value),
        "document_code": document.code,
        "document_type_id": str(document.document_type_id.value),
        "previous_status": previous_status,
        "new_status": document.status.value,
        "expected_version": str(document.version - 1),
        "resulting_version": str(document.version),
    }


class _LifecycleBase:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def _run(
        self,
        *,
        action: AuditAction,
        organization_id: Any,
        document_id: Any,
        audit_context: Any,
        mutate: Callable[
            [ComplianceDocument], tuple[ComplianceDocument, DocumentType, str]
        ],
        extra_meta: Callable[[ComplianceDocument], dict[str, str]] | None = None,
    ) -> ComplianceDocumentWithContext:
        context = require_audit_context(audit_context)
        failure_spec = AuditRecordSpec(
            action=action,
            context=context,
            resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
            resource_id=document_id.value,
            target_organization_id=organization_id,
        )

        def operation() -> tuple[ComplianceDocument, DocumentType, str]:
            existing = _load(
                self._unit_of_work,
                organization_id=organization_id,
                document_id=document_id,
            )
            previous = existing.status.value
            updated, document_type, _ = mutate(existing)
            return updated, document_type, previous

        def success_spec(
            result: tuple[ComplianceDocument, DocumentType, str],
        ) -> AuditRecordSpec:
            updated, _document_type, previous = result
            self._unit_of_work.compliance_documents.save(
                updated, expected_version=updated.version - 1
            )
            metadata = _meta(updated, previous_status=previous)
            if extra_meta is not None:
                metadata.update(extra_meta(updated))
            return AuditRecordSpec(
                action=action,
                context=context,
                resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                resource_id=updated.id.value,
                target_organization_id=updated.organization_id,
                metadata=metadata,
            )

        result = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        updated, document_type, _ = result
        return _review_due_context(updated, document_type, self._clock)


class ApproveComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: ApproveComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(
            document: ComplianceDocument,
        ) -> tuple[ComplianceDocument, DocumentType, str]:
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            updated = document.approve(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            return updated, document_type, document.status.value

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_APPROVED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
        )


class ActivateComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: ActivateComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_DOCUMENT_ACTIVATED,
            context=context,
            resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
            resource_id=command.document_id.value,
            target_organization_id=command.organization_id,
        )

        @dataclass(frozen=True, slots=True)
        class _ActivationResult:
            activated: ComplianceDocument
            document_type: DocumentType
            previous_status: str
            superseded: ComplianceDocument | None
            superseded_previous_status: str | None

        def operation() -> _ActivationResult:
            document = _load(
                self._unit_of_work,
                organization_id=command.organization_id,
                document_id=command.document_id,
            )
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            if (
                document_type.requires_approval_order
                and document.approved_by_document_id is not None
            ):
                approving = self._unit_of_work.compliance_documents.get(
                    document.organization_id,
                    document.approved_by_document_id,
                )
                if approving is None:
                    raise ComplianceDocumentValidationError(
                        "The approval order document does not exist."
                    )
                approving_type = _load_type(
                    self._unit_of_work,
                    organization_id=approving.organization_id,
                    document_type_id=approving.document_type_id,
                )
                if approving_type.code != APPROVAL_ORDER_TYPE_CODE:
                    raise ComplianceDocumentValidationError(
                        "The approval order document is not of type 'order'."
                    )
                if approving.status not in (
                    ComplianceDocumentStatus.ACTIVE,
                    ComplianceDocumentStatus.UNDER_REVIEW,
                ):
                    raise ComplianceDocumentValidationError(
                        "The approval order document is not in force."
                    )
            previous_status = document.status.value
            activated = document.activate(
                document_type=document_type,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            superseded: ComplianceDocument | None = None
            superseded_previous_status: str | None = None
            if activated.supersedes_document_id is not None:
                old = self._unit_of_work.compliance_documents.get(
                    activated.organization_id,
                    activated.supersedes_document_id,
                )
                if old is None:
                    raise ComplianceDocumentValidationError(
                        "The superseded document does not exist."
                    )
                superseded_previous_status = old.status.value
                superseded = old.supersede(
                    replacement=activated,
                    at=self._clock.now(),
                    actor_id=command.actor_id,
                    expected_version=old.version,
                )
            return _ActivationResult(
                activated=activated,
                document_type=document_type,
                previous_status=previous_status,
                superseded=superseded,
                superseded_previous_status=superseded_previous_status,
            )

        def success_spec(result: _ActivationResult) -> AuditRecordSpec:
            if (
                result.superseded is not None
                and result.superseded_previous_status is not None
            ):
                self._unit_of_work.compliance_documents.save(
                    result.superseded,
                    expected_version=result.superseded.version - 1,
                )
                self._audit.record_success(
                    self._unit_of_work,
                    AuditRecordSpec(
                        action=AuditAction.COMPLIANCE_DOCUMENT_SUPERSEDED,
                        context=context,
                        resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                        resource_id=result.superseded.id.value,
                        target_organization_id=result.superseded.organization_id,
                        metadata={
                            **_meta(
                                result.superseded,
                                previous_status=result.superseded_previous_status,
                            ),
                            "replacement_document_id": str(result.activated.id.value),
                        },
                    ),
                )
            self._unit_of_work.compliance_documents.save(
                result.activated,
                expected_version=result.activated.version - 1,
            )
            return AuditRecordSpec(
                action=AuditAction.COMPLIANCE_DOCUMENT_ACTIVATED,
                context=context,
                resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                resource_id=result.activated.id.value,
                target_organization_id=result.activated.organization_id,
                metadata=_meta(result.activated, previous_status=result.previous_status),
            )

        result = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return _review_due_context(result.activated, result.document_type, self._clock)


class StartReviewComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: StartReviewComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(
            document: ComplianceDocument,
        ) -> tuple[ComplianceDocument, DocumentType, str]:
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            updated = document.start_review(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            return updated, document_type, document.status.value

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_REVIEW_STARTED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
        )


class CompleteReviewComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: CompleteReviewComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(
            document: ComplianceDocument,
        ) -> tuple[ComplianceDocument, DocumentType, str]:
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            updated = document.complete_review(
                document_type=document_type,
                completed_on=command.completed_on,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                next_review_at=command.next_review_at,
            )
            return updated, document_type, document.status.value

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_REVIEW_COMPLETED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
        )


class ArchiveComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: ArchiveComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(
            document: ComplianceDocument,
        ) -> tuple[ComplianceDocument, DocumentType, str]:
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            updated = document.archive(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            )
            return updated, document_type, document.status.value

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_ARCHIVED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
            extra_meta=lambda _document: {"reason": command.reason},
        )


class RestoreComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: RestoreComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(
            document: ComplianceDocument,
        ) -> tuple[ComplianceDocument, DocumentType, str]:
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            updated = document.restore(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            )
            return updated, document_type, document.status.value

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_RESTORED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
            extra_meta=lambda _document: {"reason": command.reason},
        )
