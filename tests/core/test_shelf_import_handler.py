"""Workbook import handler on synthetic rows (TASK-P11-012 §3.4, AC 6–7)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from backend.core.application.commands.shelf import ImportShelfWorkbookCommand
from backend.core.application.handlers.shelf import (
    ImportReport,
    ImportShelfWorkbookHandler,
)
from backend.core.application.services.shelf_import_mapping import (
    EXCLUSION_COMMENT,
    H_DOMAIN,
    H_KIND,
    H_NOTES,
    H_SECTION,
    H_STATUS,
    H_SUBSECTION,
    H_TITLE,
    H_TYPE,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryComplianceDocumentRepository,
    InMemoryDocumentTypeRepository,
    InMemoryShelfSectionRepository,
    InMemoryShelfSlotRepository,
    InMemoryUserRepository,
)
from tests.core.audit_test_support import AdminAuditStack, make_admin_audit_stack
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    compliance_document_draft,
    make_document_type,
)
from tests.fixtures.shelf import make_section
from tests.fixtures.shelf_workbook import place_row, workbook_rows


class MovingClock:
    def __init__(self) -> None:
        self.at = FIXED_AT

    def now(self) -> datetime:
        return self.at


class Shelf:
    def __init__(self) -> None:
        self.organization_id = OrganizationId(value=uuid4())
        self.actor = UserId(value=uuid4())
        self.clock = MovingClock()
        self.sections = InMemoryShelfSectionRepository()
        self.slots = InMemoryShelfSlotRepository()
        self.documents = InMemoryComplianceDocumentRepository()
        self.types = InMemoryDocumentTypeRepository()
        self.types.add(make_document_type(organization_id=self.organization_id, code="plan"))
        self.stack: AdminAuditStack = make_admin_audit_stack(
            clock=self.clock,
            authorization_organization_id=self.organization_id,
            users=InMemoryUserRepository(),
            document_types=self.types,
            compliance_documents=self.documents,
            shelf_sections=self.sections,
            shelf_slots=self.slots,
        )

    def run(self, rows: list[dict[str, Any]], *, dry_run: bool = False) -> ImportReport:
        self.clock.at += timedelta(minutes=5)
        return ImportShelfWorkbookHandler(self.stack.uow, self.clock, self.stack.audit).handle(
            ImportShelfWorkbookCommand(
                organization_id=self.organization_id,
                actor_id=self.actor,
                rows=workbook_rows(rows),
                headers=(),
                file_sha256="ab" * 32,
                dry_run=dry_run,
                audit_context=self.stack.ctx,
            )
        )

    def slot(self, code: str) -> Any:
        slot = self.slots.get_by_code(self.organization_id, code)
        assert slot is not None
        return slot

    def events(self, action: str) -> list[Any]:
        return [
            event
            for event in self.stack.audit_events.snapshot().values()
            if event.action.value == action
        ]


def _workbook() -> list[dict[str, Any]]:
    return [
        place_row("ТрБ.01.01", **{H_SUBSECTION: "Оценка уязвимости", H_TYPE: "plan"}),
        place_row("ТрБ.01.02", **{H_SUBSECTION: "Оценка уязвимости", H_STATUS: "Есть"}),
        place_row("ТрБ.02.01", **{H_SUBSECTION: "План", H_STATUS: "Не применимо"}),
        place_row("ПожБ.01.01", **{H_SUBSECTION: "Декларация", H_KIND: "Перечень"}),
    ]


@pytest.fixture
def shelf() -> Shelf:
    return Shelf()


def test_first_run_creates_sections_subsections_and_places(shelf: Shelf) -> None:
    report = shelf.run(_workbook())

    assert report.applied and not report.dry_run
    assert (report.places_total, report.sections_total, report.subsections_total) == (4, 2, 3)
    assert report.excluded_total == 1
    assert sorted(report.created) == ["ПожБ.01.01", "ТрБ.01.01", "ТрБ.01.02", "ТрБ.02.01"]
    assert report.rejected == () and report.conflicts == ()
    assert [s.code for s in shelf.sections.list(shelf.organization_id)] == ["ПожБ", "ТрБ"]
    transport = shelf.sections.get_by_code(shelf.organization_id, "ТрБ")
    assert transport is not None
    assert transport.safety_domain is SafetyDomain.TRANSPORT_SECURITY
    assert [(s.code, s.title) for s in transport.subsections] == [
        ("ТрБ.01", "Оценка уязвимости"),
        ("ТрБ.02", "План"),
    ]
    linked_type = shelf.slot("ТрБ.01.01")
    assert linked_type.document_type_code == "plan"
    assert linked_type.import_fingerprint is not None
    assert linked_type.last_imported_at == shelf.clock.at
    excluded = shelf.slot("ТрБ.02.01")
    assert excluded.exclusion is not None
    assert excluded.exclusion.reason is SlotExclusionReason.NOT_APPLICABLE
    assert excluded.exclusion.comment == EXCLUSION_COMMENT
    assert excluded.exclusion.status_before is CuratedSlotStatus.TO_CLARIFY

    assert len(shelf.events("compliance.shelf.imported")) == 1
    assert len(shelf.events("compliance.section.created")) == 2
    assert len(shelf.events("compliance.place.created")) == 4
    assert len(shelf.events("compliance.place.excluded")) == 1
    imported = shelf.events("compliance.shelf.imported")[0]
    assert imported.metadata["created_count"] == "4"
    assert imported.metadata["file_sha256"] == "ab" * 32
    assert imported.resource_type.value == "SHELF"


def test_second_run_is_idempotent(shelf: Shelf) -> None:
    shelf.run(_workbook())
    versions = {code: shelf.slot(code).version for code in ("ТрБ.01.01", "ТрБ.02.01")}

    report = shelf.run(_workbook())

    assert sorted(report.unchanged) == ["ПожБ.01.01", "ТрБ.01.01", "ТрБ.01.02", "ТрБ.02.01"]
    assert report.created == report.updated == ()
    assert {code: shelf.slot(code).version for code in versions} == versions
    assert len(shelf.events("compliance.shelf.imported")) == 2
    assert len(shelf.events("compliance.place.created")) == 4


def test_changed_row_updates_an_untouched_place(shelf: Shelf) -> None:
    shelf.run(_workbook())
    rows = _workbook()
    rows[1] = {**rows[1], H_TITLE: "План обеспечения ТБ (новая редакция)", H_STATUS: "Не применимо"}

    report = shelf.run(rows)

    assert report.updated == ("ТрБ.01.02",)
    slot = shelf.slot("ТрБ.01.02")
    assert slot.title == "План обеспечения ТБ (новая редакция)"
    assert slot.is_excluded
    assert slot.exclusion.status_before is CuratedSlotStatus.TO_CLARIFY
    (updated,) = shelf.events("compliance.place.updated")
    assert "title" in updated.metadata["changed_fields"]

    rows[1] = {**rows[1], H_STATUS: "Есть"}
    assert shelf.run(rows).updated == ("ТрБ.01.02",)
    restored = shelf.slot("ТрБ.01.02")
    assert not restored.is_excluded
    assert restored.curated_status is CuratedSlotStatus.PRESENT
    assert len(shelf.events("compliance.place.restored")) == 1


def test_place_edited_in_safetymain_is_a_conflict_and_is_not_overwritten(shelf: Shelf) -> None:
    shelf.run(_workbook())
    edited = shelf.slot("ТрБ.01.01")
    edited = edited.update_details(
        at=shelf.clock.at,
        actor_id=shelf.actor,
        expected_version=edited.version,
        short_title="План ОТБ (куратор)",
    )
    shelf.slots.save(edited, expected_version=edited.version - 1)
    rows = _workbook()
    rows[0] = {**rows[0], H_NOTES: "Новая заметка из книги"}

    report = shelf.run(rows)

    (conflict,) = report.conflicts
    assert conflict.code == "ТрБ.01.01"
    assert set(conflict.fields) == {"short_title", "notes"}
    assert conflict.fields["notes"].workbook == "Новая заметка из книги"
    assert shelf.slot("ТрБ.01.01") == edited


def test_unchanged_row_on_an_edited_place_is_unchanged(shelf: Shelf) -> None:
    shelf.run(_workbook())
    slot = shelf.slot("ТрБ.01.02")
    edited = slot.update_details(
        at=shelf.clock.at, actor_id=shelf.actor, expected_version=slot.version, notes="куратор"
    )
    shelf.slots.save(edited, expected_version=slot.version)

    report = shelf.run(_workbook())

    assert "ТрБ.01.02" in report.unchanged
    assert shelf.slot("ТрБ.01.02").notes == "куратор"


def test_linking_a_document_is_not_a_conflict(shelf: Shelf) -> None:
    shelf.run(_workbook())
    document = compliance_document_draft(
        make_document_type(organization_id=shelf.organization_id, code="other")
    )
    slot = shelf.slot("ТрБ.01.02")
    linked = slot.link_document(
        document=document,
        linked_documents=(),
        at=shelf.clock.at,
        actor_id=shelf.actor,
        expected_version=slot.version,
    )
    shelf.slots.save(linked, expected_version=slot.version)
    rows = _workbook()
    rows[1] = {**rows[1], H_NOTES: "Обновлено"}

    report = shelf.run(rows)

    assert report.updated == ("ТрБ.01.02",)
    assert shelf.slot("ТрБ.01.02").linked_document_ids == (document.id,)


def test_place_created_in_safetymain_conflicts_with_a_workbook_row(shelf: Shelf) -> None:
    from tests.fixtures.shelf import make_slot

    section = make_section(
        organization_id=shelf.organization_id,
        code="ТрБ",
        number=10,
        title="Транспортная безопасность",
        subsections=(("01", "Оценка уязвимости"), ("02", "План")),
    )
    shelf.sections.add(section)
    shelf.slots.add(make_slot(section, code="ТрБ.01.01"))

    report = shelf.run(_workbook())

    assert [conflict.code for conflict in report.conflicts] == ["ТрБ.01.01"]
    assert "ТрБ.01.01" not in report.created


def test_places_missing_from_the_workbook_are_only_reported(shelf: Shelf) -> None:
    shelf.run(_workbook())

    report = shelf.run(_workbook()[:3])

    assert report.missing_in_workbook == ("ПожБ.01.01",)
    assert not shelf.slot("ПожБ.01.01").is_excluded


def test_any_rejected_row_blocks_the_whole_run(shelf: Shelf) -> None:
    rows = [*_workbook(), place_row("ТрБ.02.02", **{H_SUBSECTION: "План", H_KIND: "Письмо"})]

    report = shelf.run(rows)

    assert not report.applied
    assert [(r.row_number, r.column, r.value) for r in report.rejected] == [(8, H_KIND, "Письмо")]
    assert shelf.sections.list(shelf.organization_id) == ()
    assert shelf.slots.list_all(shelf.organization_id) == ()
    assert shelf.stack.audit_events.snapshot() == {}


def test_dry_run_writes_and_records_nothing(shelf: Shelf) -> None:
    report = shelf.run(_workbook(), dry_run=True)

    assert report.dry_run and not report.applied
    assert len(report.created) == 4
    assert report.sections_created == ("ПожБ", "ТрБ")
    assert shelf.slots.list_all(shelf.organization_id) == ()
    assert shelf.stack.audit_events.snapshot() == {}


def test_section_renames_and_new_subsections_are_applied(shelf: Shelf) -> None:
    shelf.run(_workbook())
    rows = [
        {**row, H_SECTION: "10 Транспортная безопасность (16-ФЗ)"}
        if row["Код"].startswith("ТрБ")
        else row
        for row in _workbook()
    ]
    rows.append(place_row("ТрБ.03.01", **{H_SECTION: "10 Транспортная безопасность (16-ФЗ)", H_SUBSECTION: "Обучение"}))

    report = shelf.run(rows)

    assert report.sections_renamed == ("ТрБ",)
    assert report.subsections_created == ("ТрБ.03",)
    assert report.created == ("ТрБ.03.01",)
    section = shelf.sections.get_by_code(shelf.organization_id, "ТрБ")
    assert section is not None and section.title == "Транспортная безопасность (16-ФЗ)"
    assert len(shelf.events("compliance.section.updated")) == 1


def test_section_number_or_domain_change_is_rejected(shelf: Shelf) -> None:
    shelf.run(_workbook())
    moved = [{**row, H_SECTION: "11 Транспортная безопасность"} if row["Код"].startswith("ТрБ") else row for row in _workbook()]
    other_domain = [{**row, H_DOMAIN: "road"} if row["Код"].startswith("ПожБ") else row for row in _workbook()]

    assert {r.column for r in shelf.run(moved).rejected} == {H_SECTION}
    assert {r.column for r in shelf.run(other_domain).rejected} == {H_DOMAIN}
