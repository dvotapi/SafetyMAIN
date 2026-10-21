from __future__ import annotations

from collections.abc import Callable
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
    document_type: DocumentType | None,
    clock: ClockContract,
) -> ComplianceDocumentWithContext:
    """Shape the response context; ``is_review_due`` needs the type only when
    the resulting document is in force."""
    if document_type is None:
        return ComplianceDocumentWithContext(
            document=document, document_type=None, is_review_due=False
        )
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


MutateResult = tuple[ComplianceDocument, DocumentType | None]
"""(updated document, resolved type when needed for review-due; else None)."""

SideEffect = Callable[
    [ComplianceDocument], tuple[tuple[ComplianceDocument, AuditRecordSpec], ...]
]
"""Extra saves+audits to perform inside the same UoW, run before the main save."""


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
        mutate: Callable[[ComplianceDocument], MutateResult],
        extra_meta: Callable[[ComplianceDocument], dict[str, str]] | None = None,
        side_effects: SideEffect | None = None,
    ) -> ComplianceDocumentWithContext:
        context = require_audit_context(audit_context)
        failure_spec = AuditRecordSpec(
            action=action,
            context=context,
            resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
            resource_id=document_id.value,
            target_organization_id=organization_id,
        )

        def operation() -> tuple[ComplianceDocument, DocumentType | None, str]:
            existing = _load(
                self._unit_of_work,
                organization_id=organization_id,
                document_id=document_id,
            )
            previous = existing.status.value
            updated, document_type = mutate(existing)
            return updated, document_type, previous

        def success_spec(
            result: tuple[ComplianceDocument, DocumentType | None, str],
        ) -> AuditRecordSpec:
            updated, _document_type, previous = result
            if side_effects is not None:
                for extra_document, extra_spec in side_effects(updated):
                    self._unit_of_work.compliance_documents.save(
                        extra_document,
                        expected_version=extra_document.version - 1,
                    )
                    self._audit.record_success(self._unit_of_work, extra_spec)
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

        updated, document_type, _ = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return _review_due_context(updated, document_type, self._clock)


class ApproveComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: ApproveComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(document: ComplianceDocument) -> MutateResult:
            updated = document.approve(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            # Still draft/approved on completion — not in force, no type needed.
            return updated, None

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

        # Captured across mutate -> side_effects for the atomic supersede.
        captured: dict[str, Any] = {}

        def mutate(document: ComplianceDocument) -> MutateResult:
            document_type = _load_type(
                self._unit_of_work,
                organization_id=document.organization_id,
                document_type_id=document.document_type_id,
            )
            self._validate_approving_order(document, document_type)
            activated = document.activate(
                document_type=document_type,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            if activated.supersedes_document_id is not None:
                old = self._unit_of_work.compliance_documents.get(
                    activated.organization_id, activated.supersedes_document_id
                )
                if old is None:
                    raise ComplianceDocumentValidationError(
                        "The superseded document does not exist."
                    )
                captured["old_previous_status"] = old.status.value
                captured["superseded"] = old.supersede(
                    replacement=activated,
                    at=self._clock.now(),
                    actor_id=command.actor_id,
                    expected_version=old.version,
                )
            return activated, document_type

        def side_effects(
            activated: ComplianceDocument,
        ) -> tuple[tuple[ComplianceDocument, AuditRecordSpec], ...]:
            superseded: ComplianceDocument | None = captured.get("superseded")
            previous: str | None = captured.get("old_previous_status")
            if superseded is None or previous is None:
                return ()
            spec = AuditRecordSpec(
                action=AuditAction.COMPLIANCE_DOCUMENT_SUPERSEDED,
                context=context,
                resource_type=AuditResourceType.COMPLIANCE_DOCUMENT,
                resource_id=superseded.id.value,
                target_organization_id=superseded.organization_id,
                metadata={
                    **_meta(superseded, previous_status=previous),
                    "replacement_document_id": str(activated.id.value),
                },
            )
            return ((superseded, spec),)

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_ACTIVATED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
            side_effects=side_effects,
        )

    def _validate_approving_order(
        self, document: ComplianceDocument, document_type: DocumentType
    ) -> None:
        if not document_type.requires_approval_order:
            return
        if document.approved_by_document_id is None:
            # Entity activate() will raise with the same user-visible error.
            return
        approving = self._unit_of_work.compliance_documents.get(
            document.organization_id, document.approved_by_document_id
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


class StartReviewComplianceDocumentHandler(_LifecycleBase):
    def handle(
        self, command: StartReviewComplianceDocumentCommand
    ) -> ComplianceDocumentWithContext:
        def mutate(document: ComplianceDocument) -> MutateResult:
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
            # Under review is in force — keep the type for ``is_review_due``.
            return updated, document_type

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
        def mutate(document: ComplianceDocument) -> MutateResult:
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
            return updated, document_type

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
        def mutate(document: ComplianceDocument) -> MutateResult:
            updated = document.archive(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            )
            # Archived is terminal; is_review_due is always False.
            return updated, None

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
        def mutate(document: ComplianceDocument) -> MutateResult:
            updated = document.restore(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                reason=command.reason,
            )
            # Restore returns to draft/approved/active/superseded. For
            # non-in-force targets ``is_review_due`` is False without a type;
            # when active/under_review it would consult the type, so load it
            # only on that branch.
            if updated.status in (
                ComplianceDocumentStatus.ACTIVE,
                ComplianceDocumentStatus.UNDER_REVIEW,
            ):
                document_type = _load_type(
                    self._unit_of_work,
                    organization_id=document.organization_id,
                    document_type_id=document.document_type_id,
                )
                return updated, document_type
            return updated, None

        return self._run(
            action=AuditAction.COMPLIANCE_DOCUMENT_RESTORED,
            organization_id=command.organization_id,
            document_id=command.document_id,
            audit_context=command.audit_context,
            mutate=mutate,
            extra_meta=lambda _document: {"reason": command.reason},
        )
