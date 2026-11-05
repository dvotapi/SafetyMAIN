"""Shared reading, view shaping and audit helpers of the shelf handlers."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
    AuditRecordSpec,
)
from backend.core.application.audit.failure_codes import AUDITABLE_ADMIN_FAILURES
from backend.core.application.queries.shelf import ShelfCapabilities
from backend.core.application.services.shelf_status_evaluator import (
    ShelfSummary,
    SlotActions,
    SlotEvaluation,
    available_actions,
    evaluate,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.shelf_section import ShelfSection, ShelfSubsection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.exceptions.shelf import (
    ShelfSlotDocumentTypeUnknown,
    ShelfSlotNotFound,
)
from backend.core.domain.exceptions.user import UserNotFound
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
    ShelfSlotId,
)

# ---- views returned to the API layer ----


@dataclass(frozen=True, slots=True)
class ShelfSlotView:
    slot: ShelfSlot
    evaluation: SlotEvaluation


@dataclass(frozen=True, slots=True)
class ShelfSlotDetailView:
    slot: ShelfSlot
    evaluation: SlotEvaluation
    actions: SlotActions
    current_document: ComplianceDocument | None
    approved_by_order: ComplianceDocument | None
    editions: tuple[ComplianceDocument, ...]
    """All linked documents, newest ``effective_from`` first, unset last."""
    excluded_by_name: str | None


@dataclass(frozen=True, slots=True)
class ShelfSectionSummaryView:
    section: ShelfSection
    summary: ShelfSummary
    strip: tuple[ShelfSlotView, ...]


@dataclass(frozen=True, slots=True)
class ShelfOverviewView:
    sections: tuple[ShelfSectionSummaryView, ...]
    totals: ShelfSummary
    evaluated_at: datetime
    last_imported_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ShelfSubsectionSlotsView:
    subsection: ShelfSubsection
    slots: tuple[ShelfSlotView, ...]


@dataclass(frozen=True, slots=True)
class ShelfSectionSlotsView:
    section: ShelfSection
    subsections: tuple[ShelfSubsectionSlotsView, ...]


@dataclass(frozen=True, slots=True)
class DevelopShelfSlotResult:
    document: ComplianceDocument
    slot: ShelfSlotDetailView


# ---- reading ----


class ShelfReader:
    """Loads what the evaluator needs with a fixed number of queries per request."""

    def __init__(self, unit_of_work: UnitOfWorkContract, organization_id: OrganizationId) -> None:
        self._unit_of_work = unit_of_work
        self._organization_id = organization_id
        self._types: dict[DocumentTypeId, DocumentType] | None = None

    def slot(self, slot_id: ShelfSlotId) -> ShelfSlot:
        slot = self._unit_of_work.shelf_slots.get(self._organization_id, slot_id)
        if slot is None:
            raise ShelfSlotNotFound(slot_id)
        return slot

    def document_types(self) -> dict[DocumentTypeId, DocumentType]:
        if self._types is None:
            self._types = {
                item.id: item
                for item in self._unit_of_work.document_types.list(
                    self._organization_id, include_inactive=True
                )
            }
        return self._types

    def active_type_by_code(self, code: str) -> DocumentType:
        document_type = self._unit_of_work.document_types.get_by_code(
            self._organization_id, code
        )
        if document_type is None or not document_type.is_active:
            raise ShelfSlotDocumentTypeUnknown(code)
        return document_type

    def documents(self, ids: Iterable[ComplianceDocumentId]) -> tuple[ComplianceDocument, ...]:
        wanted = tuple(dict.fromkeys(ids))
        if not wanted:
            return ()
        return self._unit_of_work.compliance_documents.list_by_ids(
            self._organization_id, wanted
        )

    def linked_documents(self, slot: ShelfSlot) -> tuple[ComplianceDocument, ...]:
        return self.documents(slot.linked_document_ids)

    def views(self, slots: Sequence[ShelfSlot], today: date) -> tuple[ShelfSlotView, ...]:
        documents = self.documents(
            document_id for slot in slots for document_id in slot.linked_document_ids
        )
        types = self.document_types()
        return tuple(
            ShelfSlotView(slot=slot, evaluation=evaluate(slot, documents, types, today))
            for slot in slots
        )

    def detail(
        self,
        slot: ShelfSlot,
        today: date,
        capabilities: ShelfCapabilities,
        *,
        documents: Sequence[ComplianceDocument] | None = None,
    ) -> ShelfSlotDetailView:
        """``documents`` may be passed when the caller already holds the linked ones."""
        linked = [
            document
            for document in (self.linked_documents(slot) if documents is None else documents)
            if document.id in slot.linked_document_ids
        ]
        evaluation = evaluate(slot, linked, self.document_types(), today)
        by_id = {document.id: document for document in linked}
        current = (
            by_id.get(evaluation.current_document_id)
            if evaluation.current_document_id is not None
            else None
        )
        approved_by = None
        if current is not None and current.approved_by_document_id is not None:
            approved_by = self._unit_of_work.compliance_documents.get(
                self._organization_id, current.approved_by_document_id
            )
        return ShelfSlotDetailView(
            slot=slot,
            evaluation=evaluation,
            actions=available_actions(
                evaluation,
                can_curate=capabilities.can_curate,
                can_create_document=capabilities.can_create_document,
                can_update_document=capabilities.can_update_document,
            ),
            current_document=current,
            approved_by_order=approved_by,
            editions=_editions(linked),
            excluded_by_name=self._excluded_by_name(slot),
        )

    def _excluded_by_name(self, slot: ShelfSlot) -> str | None:
        if slot.exclusion is None:
            return None
        try:
            return self._unit_of_work.users.get(slot.exclusion.excluded_by).display_name
        except UserNotFound:
            return ""


def _editions(documents: Iterable[ComplianceDocument]) -> tuple[ComplianceDocument, ...]:
    def key(document: ComplianceDocument) -> tuple[bool, int, float]:
        started = document.effective_from
        return (
            started is None,
            -(started.toordinal() if started else 0),
            -document.updated_at.timestamp(),
        )

    return tuple(sorted(documents, key=key))


# ---- audit ----


def slot_metadata(
    slot: ShelfSlot, *, previous: ShelfSlot | None = None
) -> dict[str, str]:
    """P15: identity, curated status transition and versions of a place."""
    metadata = {
        "slot_id": str(slot.id.value),
        "slot_code": slot.code.value,
        "section_code": slot.code.section_code,
        "new_status": slot.curated_status.value,
        "resulting_version": str(slot.version),
    }
    if previous is not None:
        metadata["previous_status"] = previous.curated_status.value
        metadata["expected_version"] = str(previous.version)
    return metadata


def slot_spec(
    action: AuditAction,
    context: AuditContext,
    slot: ShelfSlot,
    *,
    previous: ShelfSlot | None = None,
    **extra: str,
) -> AuditRecordSpec:
    return AuditRecordSpec(
        action=action,
        context=context,
        resource_type=AuditResourceType.SHELF_PLACE,
        resource_id=slot.id.value,
        target_organization_id=slot.organization_id,
        metadata={**slot_metadata(slot, previous=previous), **extra},
    )


def slot_failure_spec(
    action: AuditAction,
    context: AuditContext,
    organization_id: OrganizationId,
    slot_id: ShelfSlotId | None = None,
    **metadata: str,
) -> AuditRecordSpec:
    return AuditRecordSpec(
        action=action,
        context=context,
        resource_type=AuditResourceType.SHELF_PLACE,
        resource_id=slot_id.value if slot_id is not None else None,
        target_organization_id=organization_id,
        metadata=metadata or None,
    )


def run_shelf_command[T](
    audit: AdministrativeAuditRecorder,
    unit_of_work: UnitOfWorkContract,
    *,
    failure_spec: AuditRecordSpec,
    operation: Callable[[], tuple[T, Sequence[AuditRecordSpec]]],
) -> T:
    """Like ``run_audited_admin_operation`` but with zero or more success events.

    ``operation`` performs its saves and returns the result with the events to
    record in the same unit of work; an idempotent no-op returns no events.
    """
    begin = getattr(unit_of_work, "begin", None)
    if begin is not None:
        begin()
    try:
        result, specs = operation()
        for spec in specs:
            audit.record_success(unit_of_work, spec)
        unit_of_work.commit()
        return result
    except Exception as error:
        unit_of_work.rollback()
        if type(error) in AUDITABLE_ADMIN_FAILURES:
            audit.record_known_failure(failure_spec, error)
        raise
