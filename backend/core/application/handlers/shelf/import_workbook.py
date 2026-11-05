"""Workbook import (TASK-P11-012 §3.4, D3; plan phase 3 P9–P15).

The handler compares mapped rows with the stored shelf and builds a plan:

- a new place is ``created``;
- a row whose fingerprint equals the stored one is ``unchanged``;
- a changed row on a place not edited since the last import is ``updated``;
- a changed row on a place edited in SafetyMAIN is a ``conflict``: reported, not
  applied.

Places absent from the workbook are only reported. A real run applies the plan in
one unit of work with the same domain transitions and audit events as the API,
plus one ``compliance.shelf.imported``. Any rejected row blocks the whole run.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import require_audit_context
from backend.core.application.commands.shelf import ImportShelfWorkbookCommand
from backend.core.application.handlers.shelf.sections import section_spec
from backend.core.application.handlers.shelf.support import run_shelf_command, slot_spec
from backend.core.application.services.shelf_import_mapping import (
    EXCLUSION_COMMENT,
    H_CODE,
    H_DOMAIN,
    H_SECTION,
    MappedPlace,
    RowRejection,
    map_rows,
    slot_fingerprint,
    slot_values,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.exceptions.shelf import ShelfError
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.shelf_enums import SlotExclusionReason
from backend.core.domain.value_objects.shelf_values import SlotLegalBasis

REPORT_VALUE_MAX_LENGTH = 80


@dataclass(frozen=True, slots=True)
class FieldDifference:
    workbook: str
    safetymain: str


@dataclass(frozen=True, slots=True)
class ImportConflict:
    code: str
    row_number: int
    fields: dict[str, FieldDifference]


@dataclass(frozen=True, slots=True)
class ImportReport:
    dry_run: bool
    applied: bool
    places_total: int
    sections_total: int
    subsections_total: int
    excluded_total: int
    created: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()
    conflicts: tuple[ImportConflict, ...] = ()
    rejected: tuple[RowRejection, ...] = ()
    missing_in_workbook: tuple[str, ...] = ()
    sections_created: tuple[str, ...] = ()
    sections_renamed: tuple[str, ...] = ()
    subsections_created: tuple[str, ...] = ()
    subsections_renamed: tuple[str, ...] = ()
    ignored_headers: tuple[str, ...] = ()
    file_sha256: str = ""


@dataclass
class _Plan:
    sections: dict[str, ShelfSection] = field(default_factory=dict)
    section_originals: dict[str, ShelfSection | None] = field(default_factory=dict)
    section_specs: list[AuditRecordSpec] = field(default_factory=list)
    new_slots: list[ShelfSlot] = field(default_factory=list)
    changed_slots: list[tuple[ShelfSlot, ShelfSlot]] = field(default_factory=list)
    slot_specs: list[AuditRecordSpec] = field(default_factory=list)
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    conflicts: list[ImportConflict] = field(default_factory=list)
    rejected: list[RowRejection] = field(default_factory=list)
    sections_created: list[str] = field(default_factory=list)
    sections_renamed: list[str] = field(default_factory=list)
    subsections_created: list[str] = field(default_factory=list)
    subsections_renamed: list[str] = field(default_factory=list)


class ImportShelfWorkbookHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: ImportShelfWorkbookCommand) -> ImportReport:
        context = require_audit_context(command.audit_context)
        organization_id = command.organization_id
        now = self._clock.now()
        active_types = frozenset(
            item.code for item in self._unit_of_work.document_types.list(organization_id)
        )
        mapping = map_rows(
            command.rows, active_type_codes=active_types, headers=command.headers
        )
        plan = _Plan(rejected=list(mapping.rejections))
        places = self._plan_sections(mapping.places, plan, organization_id, now, context)
        for place in places:
            self._plan_place(place, plan, organization_id, command.actor_id, now, context)

        workbook_codes = {place.code for place in mapping.places}
        stored_codes = {
            slot.code.value for slot in self._unit_of_work.shelf_slots.list_all(organization_id)
        }
        missing = tuple(sorted(stored_codes - workbook_codes))
        plan.rejected.sort(key=lambda item: (item.row_number, item.column))

        def report(applied: bool) -> ImportReport:
            return ImportReport(
                dry_run=command.dry_run,
                applied=applied,
                places_total=len(mapping.places),
                sections_total=len({place.section_code for place in mapping.places}),
                subsections_total=len({place.subsection_code for place in mapping.places}),
                excluded_total=sum(1 for place in mapping.places if place.excluded),
                created=tuple(plan.created),
                updated=tuple(plan.updated),
                unchanged=tuple(plan.unchanged),
                conflicts=tuple(plan.conflicts),
                rejected=tuple(plan.rejected),
                missing_in_workbook=missing,
                sections_created=tuple(plan.sections_created),
                sections_renamed=tuple(plan.sections_renamed),
                subsections_created=tuple(plan.subsections_created),
                subsections_renamed=tuple(plan.subsections_renamed),
                ignored_headers=mapping.ignored_headers,
                file_sha256=command.file_sha256,
            )

        if command.dry_run or plan.rejected:
            return report(applied=False)

        imported_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_SHELF_IMPORTED,
            context=context,
            resource_type=AuditResourceType.SHELF,
            target_organization_id=organization_id,
            metadata={
                "file_sha256": command.file_sha256,
                "created_count": str(len(plan.created)),
                "updated_count": str(len(plan.updated)),
                "unchanged_count": str(len(plan.unchanged)),
                "conflict_count": str(len(plan.conflicts)),
                "rejected_count": "0",
                "missing_count": str(len(missing)),
            },
        )

        def operation() -> tuple[ImportReport, list[AuditRecordSpec]]:
            for code, section in plan.sections.items():
                original = plan.section_originals[code]
                if original is None:
                    self._unit_of_work.shelf_sections.add(section)
                elif section is not original:
                    self._unit_of_work.shelf_sections.save(
                        section, expected_version=original.version
                    )
            for slot in plan.new_slots:
                self._unit_of_work.shelf_slots.add(slot)
            for original, updated in plan.changed_slots:
                self._unit_of_work.shelf_slots.save(updated, expected_version=original.version)
            return report(applied=True), [
                *plan.section_specs,
                *plan.slot_specs,
                imported_spec,
            ]

        failure_spec = AuditRecordSpec(
            action=AuditAction.COMPLIANCE_SHELF_IMPORTED,
            context=context,
            resource_type=AuditResourceType.SHELF,
            target_organization_id=organization_id,
            metadata={"file_sha256": command.file_sha256},
        )
        return run_shelf_command(
            self._audit, self._unit_of_work, failure_spec=failure_spec, operation=operation
        )

    # ---- sections ----

    def _plan_sections(
        self,
        places: tuple[MappedPlace, ...],
        plan: _Plan,
        organization_id: OrganizationId,
        now: datetime,
        context: AuditContext,
    ) -> list[MappedPlace]:
        """Create or rename sections/subsections in memory; returns the places whose
        section is usable (the others are rejected)."""
        by_section: dict[str, list[MappedPlace]] = defaultdict(list)
        for place in places:
            by_section[place.section_code].append(place)
        stored_sections = {
            section.code: section
            for section in self._unit_of_work.shelf_sections.list(organization_id)
        }
        numbers_in_use = {section.number: code for code, section in stored_sections.items()}
        accepted: list[MappedPlace] = []
        for code, rows in sorted(by_section.items(), key=lambda item: item[1][0].section_number):
            first = rows[0]
            stored = stored_sections.get(code)
            problem: tuple[str, str] | None = None
            if stored is not None and stored.number != first.section_number:
                problem = (H_SECTION, f"stored number is {stored.number:02d}")
            elif stored is not None and stored.safety_domain is not first.safety_domain:
                problem = (H_DOMAIN, f"stored domain is {stored.safety_domain.value}")
            elif stored is None and numbers_in_use.get(first.section_number, code) != code:
                problem = (
                    H_SECTION,
                    (
                        f"number {first.section_number:02d} belongs to section "
                        f"{numbers_in_use[first.section_number]}"
                    ),
                )
            if problem is not None:
                plan.rejected.extend(
                    RowRejection(row.row_number, problem[0], row.section_code, problem[1])
                    for row in rows
                )
                continue
            try:
                section = self._plan_section(code, rows, stored, plan, organization_id, now, context)
            except ShelfError as error:
                plan.rejected.extend(
                    RowRejection(row.row_number, H_SECTION, code, str(error)) for row in rows
                )
                continue
            plan.sections[code] = section
            plan.section_originals[code] = stored
            accepted.extend(rows)
        return accepted

    def _plan_section(
        self,
        code: str,
        rows: list[MappedPlace],
        stored: ShelfSection | None,
        plan: _Plan,
        organization_id: OrganizationId,
        now: datetime,
        context: AuditContext,
    ) -> ShelfSection:
        first = rows[0]
        subsections: dict[str, str] = {}
        for row in sorted(rows, key=lambda item: item.subsection_code):
            subsections.setdefault(row.subsection_code, row.subsection_title)
        if stored is None:
            section = ShelfSection.create(
                organization_id=organization_id,
                code=code,
                number=first.section_number,
                title=first.section_title,
                safety_domain=first.safety_domain,
                created_at=now,
            )
            for sub_code, title in subsections.items():
                section = section.add_subsection(
                    code=sub_code, title=title, at=now, expected_version=section.version
                )
            plan.sections_created.append(code)
            plan.subsections_created.extend(subsections)
            plan.section_specs.append(
                section_spec(AuditAction.COMPLIANCE_SECTION_CREATED, context, section)
            )
            return section

        section = stored
        changed: list[str] = []
        if section.title != first.section_title:
            section = section.rename(
                title=first.section_title, at=now, expected_version=section.version
            )
            plan.sections_renamed.append(code)
            changed.append("title")
        for sub_code, title in subsections.items():
            existing = section.subsection(sub_code)
            if existing is None:
                section = section.add_subsection(
                    code=sub_code, title=title, at=now, expected_version=section.version
                )
                plan.subsections_created.append(sub_code)
                changed.append("subsections")
            elif existing.title != title:
                section = section.rename_subsection(
                    code=sub_code, title=title, at=now, expected_version=section.version
                )
                plan.subsections_renamed.append(sub_code)
                changed.append("subsections")
        if changed:
            plan.section_specs.append(
                section_spec(
                    AuditAction.COMPLIANCE_SECTION_UPDATED,
                    context,
                    section,
                    previous=stored,
                    changed_fields=",".join(sorted(set(changed))),
                )
            )
        return section

    # ---- places ----

    def _plan_place(
        self,
        place: MappedPlace,
        plan: _Plan,
        organization_id: OrganizationId,
        actor: UserId,
        now: datetime,
        context: AuditContext,
    ) -> None:
        stored = self._unit_of_work.shelf_slots.get_by_code(organization_id, place.code)
        try:
            if stored is None:
                self._plan_new(place, plan, organization_id, actor, now, context)
            else:
                self._plan_existing(place, stored, plan, actor, now, context)
        except ShelfError as error:
            plan.rejected.append(RowRejection(place.row_number, H_CODE, place.code, str(error)))

    def _plan_new(
        self,
        place: MappedPlace,
        plan: _Plan,
        organization_id: OrganizationId,
        actor: UserId,
        now: datetime,
        context: AuditContext,
    ) -> None:
        values = dict(place.values)
        values["legal_basis"] = _basis(values["legal_basis"])
        slot = ShelfSlot.create(
            organization_id=organization_id,
            section=plan.sections[place.section_code],
            code=place.code,
            created_by=actor,
            created_at=now,
            import_fingerprint=place.fingerprint,
            **values,
        )
        specs = [slot_spec(AuditAction.COMPLIANCE_PLACE_CREATED, context, slot)]
        if place.excluded:
            created = slot
            slot = slot.exclude(
                reason=SlotExclusionReason.NOT_APPLICABLE,
                comment=EXCLUSION_COMMENT,
                at=now,
                actor_id=actor,
                expected_version=slot.version,
            )
            specs.append(_excluded_spec(context, slot, created))
        plan.new_slots.append(slot)
        plan.slot_specs.extend(specs)
        plan.created.append(place.code)

    def _plan_existing(
        self,
        place: MappedPlace,
        stored: ShelfSlot,
        plan: _Plan,
        actor: UserId,
        now: datetime,
        context: AuditContext,
    ) -> None:
        row_fingerprint = place.fingerprint
        if stored.import_fingerprint == row_fingerprint:
            plan.unchanged.append(place.code)
            return
        if stored.import_fingerprint is None or slot_fingerprint(stored) != stored.import_fingerprint:
            plan.conflicts.append(
                ImportConflict(
                    code=place.code,
                    row_number=place.row_number,
                    fields=_differences(place, stored),
                )
            )
            return

        values = dict(place.values)
        values["legal_basis"] = _basis(values["legal_basis"])
        slot = stored
        specs: list[AuditRecordSpec] = []
        if slot.is_excluded and not place.excluded:
            restored = slot.restore(at=now, actor_id=actor, expected_version=slot.version)
            specs.append(slot_spec(AuditAction.COMPLIANCE_PLACE_RESTORED, context, restored, previous=slot))
            slot = restored
        if slot.is_excluded:
            values.pop("curated_status")
        before = slot
        slot = slot.apply_import(
            values=values,
            fingerprint=row_fingerprint,
            at=now,
            actor_id=actor,
            expected_version=slot.version,
        )
        changed = sorted(
            name for name, value in slot_values(slot).items() if slot_values(before)[name] != value
        )
        specs.append(
            slot_spec(
                AuditAction.COMPLIANCE_PLACE_UPDATED,
                context,
                slot,
                previous=before,
                changed_fields=",".join(changed),
            )
        )
        if place.excluded and not slot.is_excluded:
            excluded = slot.exclude(
                reason=SlotExclusionReason.NOT_APPLICABLE,
                comment=EXCLUSION_COMMENT,
                at=now,
                actor_id=actor,
                expected_version=slot.version,
            )
            specs.append(_excluded_spec(context, excluded, slot))
            slot = excluded
        plan.changed_slots.append((stored, slot))
        plan.slot_specs.extend(specs)
        plan.updated.append(place.code)


def _basis(values: dict[str, Any]) -> SlotLegalBasis:
    return SlotLegalBasis(**values)


def _excluded_spec(context: AuditContext, slot: ShelfSlot, previous: ShelfSlot) -> AuditRecordSpec:
    assert slot.exclusion is not None
    return slot_spec(
        AuditAction.COMPLIANCE_PLACE_EXCLUDED,
        context,
        slot,
        previous=previous,
        reason=slot.exclusion.reason.value,
        comment=slot.exclusion.comment,
    )


def _shown(value: Any) -> str:
    if isinstance(value, Enum):
        value = value.value
    text = "" if value is None else str(value)
    return text if len(text) <= REPORT_VALUE_MAX_LENGTH else text[: REPORT_VALUE_MAX_LENGTH - 1] + "…"


def _differences(place: MappedPlace, stored: ShelfSlot) -> dict[str, FieldDifference]:
    current = slot_values(stored)
    differences: dict[str, FieldDifference] = {}
    for name, workbook_value in place.values.items():
        stored_value = current[name]
        if name == "legal_basis":
            for key, item in workbook_value.items():
                if _shown(item) != _shown(stored_value[key]):
                    differences[f"legal_basis.{key}"] = FieldDifference(
                        workbook=_shown(item), safetymain=_shown(stored_value[key])
                    )
            continue
        if name == "curated_status":
            workbook_status = "excluded" if place.excluded else _shown(workbook_value)
            stored_status = "excluded" if stored.is_excluded else _shown(stored_value)
            if workbook_status != stored_status:
                differences["status"] = FieldDifference(workbook_status, stored_status)
            continue
        if _shown(workbook_value) != _shown(stored_value):
            differences[name] = FieldDifference(_shown(workbook_value), _shown(stored_value))
    return differences
