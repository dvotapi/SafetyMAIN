"""Curator commands on shelf places (TASK-P11-012 §2.5).

Each command loads the place in the caller's organization (foreign → 404),
applies one domain transition, saves with optimistic concurrency and records
``compliance.place.*`` in the same unit of work. The response view is shaped
before commit so it reflects exactly what was saved.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import require_audit_context
from backend.core.application.commands.compliance_documents import (
    CreateComplianceDocumentCommand,
)
from backend.core.application.commands.shelf import (
    BulkExcludeShelfSlotsCommand,
    ConfirmShelfSlotApplicableCommand,
    CreateShelfSlotCommand,
    DevelopShelfSlotDocumentCommand,
    ExcludeShelfSlotCommand,
    LinkShelfSlotDocumentCommand,
    RestoreShelfSlotCommand,
    UnlinkShelfSlotDocumentCommand,
    UpdateShelfSlotCommand,
)
from backend.core.application.handlers.compliance_documents.create_compliance_document import (
    build_compliance_document,
    document_created_audit_spec,
)
from backend.core.application.handlers.shelf.support import (
    DevelopShelfSlotResult,
    ShelfReader,
    ShelfSlotDetailView,
    ShelfSlotView,
    run_shelf_command,
    slot_failure_spec,
    slot_spec,
)
from backend.core.application.queries.shelf import ShelfCapabilities
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.exceptions.shelf import (
    ShelfSlotCodeMismatch,
    ShelfSlotDocumentNotFound,
    ShelfSlotDocumentTypeRequired,
    ShelfSlotsAlreadyExcluded,
    ShelfSlotsVersionConflict,
    ShelfSlotValidationError,
    ShelfSlotVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentSource
from backend.core.domain.value_objects.safety_ids import ShelfSlotId
from backend.core.domain.value_objects.shelf_slot_code import ShelfSlotCode

BULK_EXCLUDE_MAX_ITEMS = 200

CURATOR = ShelfCapabilities(can_curate=True, can_create_document=True)
"""Default capabilities of a command caller (the router passes the real ones)."""


class _SlotHandlerBase:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def _transition(
        self,
        *,
        action: AuditAction,
        organization_id: OrganizationId,
        slot_id: ShelfSlotId,
        audit_context: AuditContext | None,
        capabilities: ShelfCapabilities,
        mutate: Callable[[ShelfSlot], ShelfSlot],
        extra_metadata: Callable[[ShelfSlot], dict[str, str]] | None = None,
    ) -> ShelfSlotDetailView:
        """Load, mutate, save and audit one place; an unchanged place is a no-op."""
        context = require_audit_context(audit_context)
        failure_spec = slot_failure_spec(action, context, organization_id, slot_id)
        reader = ShelfReader(self._unit_of_work, organization_id)

        def operation() -> tuple[ShelfSlotDetailView, tuple[AuditRecordSpec, ...]]:
            existing = reader.slot(slot_id)
            updated = mutate(existing)
            view = reader.detail(updated, self._today(), capabilities)
            if updated is existing:
                return view, ()
            self._unit_of_work.shelf_slots.save(updated, expected_version=existing.version)
            extra = extra_metadata(updated) if extra_metadata is not None else {}
            return view, (slot_spec(action, context, updated, previous=existing, **extra),)

        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )

    def _today(self) -> date:
        return self._clock.now().date()


class CreateShelfSlotHandler(_SlotHandlerBase):
    def handle(
        self,
        command: CreateShelfSlotCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        context = require_audit_context(command.audit_context)
        failure_spec = slot_failure_spec(
            AuditAction.COMPLIANCE_PLACE_CREATED,
            context,
            command.organization_id,
            slot_code=command.code,
        )
        reader = ShelfReader(self._unit_of_work, command.organization_id)

        def operation() -> tuple[ShelfSlotDetailView, tuple[AuditRecordSpec, ...]]:
            try:
                code = ShelfSlotCode(value=command.code)
            except ValueError as error:
                raise ShelfSlotValidationError(str(error)) from error
            section = self._unit_of_work.shelf_sections.get_by_code(
                command.organization_id, code.section_code
            )
            if section is None:
                raise ShelfSlotCodeMismatch(code=command.code, section_code=code.section_code)
            if command.document_type_code:
                reader.active_type_by_code(command.document_type_code)
            slot = ShelfSlot.create(
                organization_id=command.organization_id,
                section=section,
                code=command.code,
                title=command.title,
                short_title=command.short_title,
                document_kind=command.document_kind,
                kept_on=command.kept_on,
                obligation_level=command.obligation_level,
                curated_status=command.curated_status,
                created_by=command.actor_id,
                created_at=self._clock.now(),
                applicability_condition=command.applicability_condition,
                legal_basis=command.legal_basis,
                review_cycle_text=command.review_cycle_text,
                review_period_months=command.review_period_months,
                document_type_code=command.document_type_code,
                proposed_document_type=command.proposed_document_type,
                responsible_text=command.responsible_text,
                legacy_location=command.legacy_location,
                notes=command.notes,
                package_code=command.package_code,
                legacy_code=command.legacy_code,
            )
            self._unit_of_work.shelf_slots.add(slot)
            view = reader.detail(slot, self._today(), capabilities, documents=())
            return view, (slot_spec(AuditAction.COMPLIANCE_PLACE_CREATED, context, slot),)

        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )


class UpdateShelfSlotHandler(_SlotHandlerBase):
    def handle(
        self,
        command: UpdateShelfSlotCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        reader = ShelfReader(self._unit_of_work, command.organization_id)
        changes = dict(command.changes)

        def mutate(slot: ShelfSlot) -> ShelfSlot:
            new_code = changes.get("document_type_code")
            if new_code and new_code != slot.document_type_code:
                reader.active_type_by_code(new_code)
            return slot.update_details(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
                **changes,
            )

        def changed_fields(_updated: ShelfSlot) -> dict[str, str]:
            return {"changed_fields": ",".join(sorted(changes))}

        return self._transition(
            action=AuditAction.COMPLIANCE_PLACE_UPDATED,
            organization_id=command.organization_id,
            slot_id=command.slot_id,
            audit_context=command.audit_context,
            capabilities=capabilities,
            mutate=mutate,
            extra_metadata=changed_fields,
        )


class ExcludeShelfSlotHandler(_SlotHandlerBase):
    def handle(
        self,
        command: ExcludeShelfSlotCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        return self._transition(
            action=AuditAction.COMPLIANCE_PLACE_EXCLUDED,
            organization_id=command.organization_id,
            slot_id=command.slot_id,
            audit_context=command.audit_context,
            capabilities=capabilities,
            mutate=lambda slot: slot.exclude(
                reason=command.reason,
                comment=command.comment,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
            extra_metadata=_exclusion_metadata,
        )


class RestoreShelfSlotHandler(_SlotHandlerBase):
    def handle(
        self,
        command: RestoreShelfSlotCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        return self._transition(
            action=AuditAction.COMPLIANCE_PLACE_RESTORED,
            organization_id=command.organization_id,
            slot_id=command.slot_id,
            audit_context=command.audit_context,
            capabilities=capabilities,
            mutate=lambda slot: slot.restore(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
        )


class ConfirmShelfSlotApplicableHandler(_SlotHandlerBase):
    def handle(
        self,
        command: ConfirmShelfSlotApplicableCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        return self._transition(
            action=AuditAction.COMPLIANCE_PLACE_CONFIRMED,
            organization_id=command.organization_id,
            slot_id=command.slot_id,
            audit_context=command.audit_context,
            capabilities=capabilities,
            mutate=lambda slot: slot.confirm_applicable(
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            ),
        )


class LinkShelfSlotDocumentHandler(_SlotHandlerBase):
    def handle(
        self,
        command: LinkShelfSlotDocumentCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        reader = ShelfReader(self._unit_of_work, command.organization_id)
        captured: dict[str, str] = {}

        def mutate(slot: ShelfSlot) -> ShelfSlot:
            document = self._unit_of_work.compliance_documents.get(
                command.organization_id, command.document_id
            )
            if document is None:
                raise ShelfSlotDocumentNotFound(command.document_id)
            captured["document_code"] = document.code
            return slot.link_document(
                document=document,
                linked_documents=reader.linked_documents(slot),
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )

        return self._transition(
            action=AuditAction.COMPLIANCE_PLACE_LINKED,
            organization_id=command.organization_id,
            slot_id=command.slot_id,
            audit_context=command.audit_context,
            capabilities=capabilities,
            mutate=mutate,
            extra_metadata=lambda _slot: {
                "document_id": str(command.document_id.value),
                "document_code": captured["document_code"],
            },
        )


class UnlinkShelfSlotDocumentHandler(_SlotHandlerBase):
    def handle(
        self,
        command: UnlinkShelfSlotDocumentCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> ShelfSlotDetailView:
        captured: dict[str, str] = {}

        def mutate(slot: ShelfSlot) -> ShelfSlot:
            updated = slot.unlink_document(
                document_id=command.document_id,
                at=self._clock.now(),
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            document = self._unit_of_work.compliance_documents.get(
                command.organization_id, command.document_id
            )
            captured["document_code"] = document.code if document is not None else ""
            return updated

        return self._transition(
            action=AuditAction.COMPLIANCE_PLACE_UNLINKED,
            organization_id=command.organization_id,
            slot_id=command.slot_id,
            audit_context=command.audit_context,
            capabilities=capabilities,
            mutate=mutate,
            extra_metadata=lambda _slot: {
                "document_id": str(command.document_id.value),
                "document_code": captured["document_code"],
            },
        )


class BulkExcludeShelfSlotsHandler(_SlotHandlerBase):
    """All-or-nothing (P19): every place is checked before any is changed."""

    def handle(self, command: BulkExcludeShelfSlotsCommand) -> tuple[ShelfSlotView, ...]:
        context = require_audit_context(command.audit_context)
        failure_spec = slot_failure_spec(
            AuditAction.COMPLIANCE_PLACE_EXCLUDED, context, command.organization_id
        )
        reader = ShelfReader(self._unit_of_work, command.organization_id)

        def operation() -> tuple[tuple[ShelfSlotView, ...], tuple[AuditRecordSpec, ...]]:
            ids = [slot_id for slot_id, _ in command.items]
            if not 1 <= len(ids) <= BULK_EXCLUDE_MAX_ITEMS:
                raise ShelfSlotValidationError(
                    f"Bulk exclusion takes 1 to {BULK_EXCLUDE_MAX_ITEMS} places."
                )
            if len(set(ids)) != len(ids):
                raise ShelfSlotValidationError("Bulk exclusion lists a place more than once.")
            slots = [reader.slot(slot_id) for slot_id in ids]
            conflicts = tuple(
                slot.id
                for slot, (_, expected) in zip(slots, command.items, strict=True)
                if slot.version != expected
            )
            if conflicts:
                raise ShelfSlotsVersionConflict(conflicts)
            excluded = tuple(slot.id for slot in slots if slot.is_excluded)
            if excluded:
                raise ShelfSlotsAlreadyExcluded(excluded)
            now = self._clock.now()
            updated: list[ShelfSlot] = []
            specs: list[AuditRecordSpec] = []
            for slot in slots:
                result = slot.exclude(
                    reason=command.reason,
                    comment=command.comment,
                    at=now,
                    actor_id=command.actor_id,
                    expected_version=slot.version,
                )
                updated.append(result)
                specs.append(
                    slot_spec(
                        AuditAction.COMPLIANCE_PLACE_EXCLUDED,
                        context,
                        result,
                        previous=slot,
                        **_exclusion_metadata(result),
                    )
                )
            for previous, result in zip(slots, updated, strict=True):
                self._unit_of_work.shelf_slots.save(result, expected_version=previous.version)
            return reader.views(updated, now.date()), tuple(specs)

        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )


class DevelopShelfSlotDocumentHandler(_SlotHandlerBase):
    """Create a draft document from the place and link it atomically (P7, P12)."""

    def handle(
        self,
        command: DevelopShelfSlotDocumentCommand,
        *,
        capabilities: ShelfCapabilities = CURATOR,
    ) -> DevelopShelfSlotResult:
        context = require_audit_context(command.audit_context)
        failure_spec = slot_failure_spec(
            AuditAction.COMPLIANCE_PLACE_LINKED,
            context,
            command.organization_id,
            command.slot_id,
        )
        reader = ShelfReader(self._unit_of_work, command.organization_id)

        def operation() -> tuple[DevelopShelfSlotResult, Sequence[AuditRecordSpec]]:
            slot = reader.slot(command.slot_id)
            if slot.version != command.expected_version:
                # Checked before any work; link_document checks it again.
                raise ShelfSlotVersionConflict(
                    slot_id=slot.id,
                    expected_version=command.expected_version,
                    actual_version=slot.version,
                )
            linked = reader.linked_documents(slot)
            slot.ensure_can_develop(linked)
            type_code = command.document_type_code or slot.document_type_code
            if not type_code:
                raise ShelfSlotDocumentTypeRequired(slot.id)
            document_type = reader.active_type_by_code(type_code)
            now = self._clock.now()
            document = build_compliance_document(
                self._unit_of_work,
                CreateComplianceDocumentCommand(
                    organization_id=command.organization_id,
                    actor_id=command.actor_id,
                    document_type_id=document_type.id,
                    code=slot.code.value,
                    title=slot.title,
                    source=ComplianceDocumentSource.MANUAL,
                    audit_context=context,
                ),
                now=now,
            )
            updated = slot.link_document(
                document=document,
                linked_documents=linked,
                at=now,
                actor_id=command.actor_id,
                expected_version=command.expected_version,
            )
            self._unit_of_work.compliance_documents.add(document)
            self._unit_of_work.shelf_slots.save(updated, expected_version=slot.version)
            view = reader.detail(
                updated, now.date(), capabilities, documents=(*linked, document)
            )
            return DevelopShelfSlotResult(document=document, slot=view), (
                document_created_audit_spec(document, context),
                slot_spec(
                    AuditAction.COMPLIANCE_PLACE_LINKED,
                    context,
                    updated,
                    previous=slot,
                    document_id=str(document.id.value),
                    document_code=document.code,
                ),
            )

        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )


def _exclusion_metadata(slot: ShelfSlot) -> dict[str, str]:
    assert slot.exclusion is not None
    return {"reason": slot.exclusion.reason.value, "comment": slot.exclusion.comment}


__all__ = [
    "BULK_EXCLUDE_MAX_ITEMS",
    "BulkExcludeShelfSlotsHandler",
    "ConfirmShelfSlotApplicableHandler",
    "CreateShelfSlotHandler",
    "DevelopShelfSlotDocumentHandler",
    "ExcludeShelfSlotHandler",
    "LinkShelfSlotDocumentHandler",
    "RestoreShelfSlotHandler",
    "UnlinkShelfSlotDocumentHandler",
    "UpdateShelfSlotHandler",
]
