"""Shelf section commands (P13): used by tests and the phase 3 importer, no HTTP yet."""

from __future__ import annotations

from collections.abc import Callable

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import require_audit_context
from backend.core.application.commands.shelf import (
    AddShelfSubsectionCommand,
    CreateShelfSectionCommand,
    RenameShelfSectionCommand,
    RenameShelfSubsectionCommand,
)
from backend.core.application.handlers.shelf.support import run_shelf_command
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.exceptions.shelf import ShelfSectionNotFound
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.safety_ids import ShelfSectionId


def _section_spec(
    action: AuditAction,
    context: AuditContext,
    section: ShelfSection,
    *,
    previous: ShelfSection | None = None,
    changed_fields: str | None = None,
    subsection_code: str | None = None,
) -> AuditRecordSpec:
    metadata = {
        "section_id": str(section.id.value),
        "section_code": section.code,
        "resulting_version": str(section.version),
    }
    if previous is not None:
        metadata["expected_version"] = str(previous.version)
    if changed_fields:
        metadata["changed_fields"] = changed_fields
    if subsection_code:
        metadata["subsection_code"] = subsection_code
    return AuditRecordSpec(
        action=action,
        context=context,
        resource_type=AuditResourceType.SHELF_SECTION,
        resource_id=section.id.value,
        target_organization_id=section.organization_id,
        metadata=metadata,
    )


class _SectionHandlerBase:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def _update(
        self,
        *,
        organization_id: OrganizationId,
        section_id: ShelfSectionId,
        audit_context: AuditContext | None,
        mutate: Callable[[ShelfSection], ShelfSection],
        changed_fields: str,
        subsection_code: str | None = None,
    ) -> ShelfSection:
        context = require_audit_context(audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_SECTION_UPDATED,
            context=context,
            resource_type=AuditResourceType.SHELF_SECTION,
            resource_id=section_id.value,
            target_organization_id=organization_id,
        )

        def operation() -> tuple[ShelfSection, tuple[AuditRecordSpec, ...]]:
            existing = self._unit_of_work.shelf_sections.get(organization_id, section_id)
            if existing is None:
                raise ShelfSectionNotFound(section_id)
            updated = mutate(existing)
            self._unit_of_work.shelf_sections.save(updated, expected_version=existing.version)
            return updated, (
                _section_spec(
                    AuditAction.COMPLIANCE_SECTION_UPDATED,
                    context,
                    updated,
                    previous=existing,
                    changed_fields=changed_fields,
                    subsection_code=subsection_code,
                ),
            )

        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )


class CreateShelfSectionHandler(_SectionHandlerBase):
    def handle(self, command: CreateShelfSectionCommand) -> ShelfSection:
        context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_SECTION_CREATED,
            context=context,
            resource_type=AuditResourceType.SHELF_SECTION,
            target_organization_id=command.organization_id,
            metadata={"section_code": command.code},
        )

        def operation() -> tuple[ShelfSection, tuple[AuditRecordSpec, ...]]:
            now = self._clock.now()
            section = ShelfSection.create(
                organization_id=command.organization_id,
                code=command.code,
                number=command.number,
                title=command.title,
                safety_domain=command.safety_domain,
                created_at=now,
                section_id=command.section_id,
            )
            for code, title in command.subsections:
                section = section.add_subsection(
                    code=code, title=title, at=now, expected_version=section.version
                )
            self._unit_of_work.shelf_sections.add(section)
            return section, (
                _section_spec(AuditAction.COMPLIANCE_SECTION_CREATED, context, section),
            )

        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )


class RenameShelfSectionHandler(_SectionHandlerBase):
    def handle(self, command: RenameShelfSectionCommand) -> ShelfSection:
        return self._update(
            organization_id=command.organization_id,
            section_id=command.section_id,
            audit_context=command.audit_context,
            mutate=lambda section: section.rename(
                title=command.title,
                at=self._clock.now(),
                expected_version=command.expected_version,
            ),
            changed_fields="title",
        )


class AddShelfSubsectionHandler(_SectionHandlerBase):
    def handle(self, command: AddShelfSubsectionCommand) -> ShelfSection:
        return self._update(
            organization_id=command.organization_id,
            section_id=command.section_id,
            audit_context=command.audit_context,
            mutate=lambda section: section.add_subsection(
                code=command.code,
                title=command.title,
                at=self._clock.now(),
                expected_version=command.expected_version,
            ),
            changed_fields="subsections",
            subsection_code=command.code,
        )


class RenameShelfSubsectionHandler(_SectionHandlerBase):
    def handle(self, command: RenameShelfSubsectionCommand) -> ShelfSection:
        return self._update(
            organization_id=command.organization_id,
            section_id=command.section_id,
            audit_context=command.audit_context,
            mutate=lambda section: section.rename_subsection(
                code=command.code,
                title=command.title,
                at=self._clock.now(),
                expected_version=command.expected_version,
            ),
            changed_fields="subsections",
            subsection_code=command.code,
        )
