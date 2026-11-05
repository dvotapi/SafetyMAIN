"""Shelf handlers without HTTP: section commands (P13) and develop atomicity (P12)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

from backend.core.application.commands.shelf import (
    AddShelfSubsectionCommand,
    CreateShelfSectionCommand,
    DevelopShelfSlotDocumentCommand,
    RenameShelfSectionCommand,
    RenameShelfSubsectionCommand,
)
from backend.core.application.handlers.shelf import (
    AddShelfSubsectionHandler,
    CreateShelfSectionHandler,
    DevelopShelfSlotDocumentHandler,
    RenameShelfSectionHandler,
    RenameShelfSubsectionHandler,
)
from backend.core.domain.exceptions.shelf import (
    DuplicateShelfSectionCode,
    ShelfSectionVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryComplianceDocumentRepository,
    InMemoryDocumentTypeRepository,
    InMemoryShelfSectionRepository,
    InMemoryShelfSlotRepository,
    InMemoryUserRepository,
)
from tests.core.audit_test_support import AdminAuditStack, make_admin_audit_stack
from tests.fixtures.compliance_documents import FIXED_AT, make_document_type
from tests.fixtures.shelf import make_section, make_slot


class FixedClock:
    def now(self) -> datetime:
        return FIXED_AT


def _stack(organization_id: OrganizationId, **repositories: object) -> AdminAuditStack:
    defaults: dict[str, object] = {
        "users": InMemoryUserRepository(),
        "document_types": InMemoryDocumentTypeRepository(),
        "compliance_documents": InMemoryComplianceDocumentRepository(),
        "shelf_sections": InMemoryShelfSectionRepository(),
        "shelf_slots": InMemoryShelfSlotRepository(),
    }
    return make_admin_audit_stack(
        clock=FixedClock(),
        authorization_organization_id=organization_id,
        **{**defaults, **repositories},
    )


def _actions(stack: AdminAuditStack) -> list[tuple[str, str | None]]:
    return [
        (event.action.value, event.failure_code)
        for event in sorted(stack.audit_events.snapshot().values(), key=lambda e: e.occurred_at)
    ]


def test_section_commands_create_rename_and_extend_with_audit() -> None:
    organization_id = OrganizationId(value=uuid4())
    stack = _stack(organization_id)
    actor = UserId(value=uuid4())

    section = CreateShelfSectionHandler(stack.uow, FixedClock(), stack.audit).handle(
        CreateShelfSectionCommand(
            organization_id=organization_id,
            actor_id=actor,
            code="ТрБ",
            number=10,
            title="Транспортная безопасность",
            safety_domain=SafetyDomain.TRANSPORT_SECURITY,
            subsections=(("ТрБ.01", "Оценка уязвимости"),),
            audit_context=stack.ctx,
        )
    )
    renamed = RenameShelfSectionHandler(stack.uow, FixedClock(), stack.audit).handle(
        RenameShelfSectionCommand(
            organization_id=organization_id,
            section_id=section.id,
            actor_id=actor,
            expected_version=section.version,
            title="ТрБез",
            audit_context=stack.ctx,
        )
    )
    extended = AddShelfSubsectionHandler(stack.uow, FixedClock(), stack.audit).handle(
        AddShelfSubsectionCommand(
            organization_id=organization_id,
            section_id=section.id,
            actor_id=actor,
            expected_version=renamed.version,
            code="ТрБ.02",
            title="План",
            audit_context=stack.ctx,
        )
    )
    final = RenameShelfSubsectionHandler(stack.uow, FixedClock(), stack.audit).handle(
        RenameShelfSubsectionCommand(
            organization_id=organization_id,
            section_id=section.id,
            actor_id=actor,
            expected_version=extended.version,
            code="ТрБ.02",
            title="План обеспечения",
            audit_context=stack.ctx,
        )
    )

    stored = stack.uow.shelf_sections.get(organization_id, section.id)
    assert stored == final
    assert final.title == "ТрБез"
    assert [item.code for item in final.subsections] == ["ТрБ.01", "ТрБ.02"]
    assert final.subsections[1].title == "План обеспечения"
    assert _actions(stack) == [
        ("compliance.section.created", None),
        ("compliance.section.updated", None),
        ("compliance.section.updated", None),
        ("compliance.section.updated", None),
    ]
    resource_types = {event.resource_type.value for event in stack.audit_events.snapshot().values()}
    assert resource_types == {"SHELF_SECTION"}


def test_section_failures_are_audited() -> None:
    organization_id = OrganizationId(value=uuid4())
    sections = InMemoryShelfSectionRepository()
    existing = make_section(organization_id=organization_id)
    sections.add(existing)
    stack = _stack(organization_id, shelf_sections=sections)
    actor = UserId(value=uuid4())

    with pytest.raises(DuplicateShelfSectionCode):
        CreateShelfSectionHandler(stack.uow, FixedClock(), stack.audit).handle(
            CreateShelfSectionCommand(
                organization_id=organization_id,
                actor_id=actor,
                code=existing.code,
                number=99,
                title="Дубль",
                safety_domain=SafetyDomain.FIRE,
                audit_context=stack.ctx,
            )
        )
    with pytest.raises(ShelfSectionVersionConflict):
        RenameShelfSectionHandler(stack.uow, FixedClock(), stack.audit).handle(
            RenameShelfSectionCommand(
                organization_id=organization_id,
                section_id=existing.id,
                actor_id=actor,
                expected_version=existing.version + 5,
                title="Устарело",
                audit_context=stack.ctx,
            )
        )

    assert _actions(stack) == [
        ("compliance.section.created", "duplicate_shelf_section_code"),
        ("compliance.section.updated", "shelf_section_version_conflict"),
    ]


class _FailingSlots(InMemoryShelfSlotRepository):
    def save(self, slot: object, *, expected_version: int) -> None:  # type: ignore[override]
        raise RuntimeError("storage failure after the document was added")


def test_develop_rolls_back_the_document_when_the_place_cannot_be_saved() -> None:
    organization_id = OrganizationId(value=uuid4())
    document_types = InMemoryDocumentTypeRepository()
    document_types.add(make_document_type(organization_id=organization_id, code="plan"))
    documents = InMemoryComplianceDocumentRepository()
    sections = InMemoryShelfSectionRepository()
    slots = _FailingSlots()
    section = make_section(organization_id=organization_id)
    sections.add(section)
    slot = make_slot(section, document_type_code="plan")
    slots.add(slot)
    stack = _stack(
        organization_id,
        document_types=document_types,
        compliance_documents=documents,
        shelf_sections=sections,
        shelf_slots=slots,
    )

    with pytest.raises(RuntimeError):
        DevelopShelfSlotDocumentHandler(stack.uow, FixedClock(), stack.audit).handle(
            DevelopShelfSlotDocumentCommand(
                organization_id=organization_id,
                slot_id=slot.id,
                actor_id=UserId(value=uuid4()),
                expected_version=1,
                audit_context=stack.ctx,
            )
        )

    assert documents.snapshot() == {}
    assert slots.get(organization_id, slot.id) == slot
    assert _actions(stack) == []


class _CountingDocuments(InMemoryComplianceDocumentRepository):
    def __init__(self) -> None:
        super().__init__()
        self.list_by_ids_calls = 0
        self.get_calls = 0

    def list_by_ids(self, organization_id, document_ids):  # type: ignore[no-untyped-def]
        self.list_by_ids_calls += 1
        return super().list_by_ids(organization_id, document_ids)

    def get(self, organization_id, document_id):  # type: ignore[no-untyped-def]
        self.get_calls += 1
        return super().get(organization_id, document_id)


def test_overview_of_500_places_loads_documents_in_one_query() -> None:
    from backend.core.application.handlers.shelf import GetShelfOverviewHandler
    from backend.core.application.queries.shelf import GetShelfOverviewQuery

    organization_id = OrganizationId(value=uuid4())
    sections = InMemoryShelfSectionRepository()
    slots = InMemoryShelfSlotRepository()
    documents = _CountingDocuments()
    section = make_section(
        organization_id=organization_id,
        subsections=tuple((f"{number:02d}", f"Подраздел {number}") for number in range(1, 26)),
    )
    sections.add(section)
    for subsection in range(1, 26):
        for place in range(1, 21):
            slots.add(make_slot(section, code=f"ТрБ.{subsection:02d}.{place:02d}"))
    stack = _stack(
        organization_id, shelf_sections=sections, shelf_slots=slots, compliance_documents=documents
    )

    overview = GetShelfOverviewHandler(stack.uow, FixedClock()).handle(
        GetShelfOverviewQuery(organization_id=organization_id)
    )

    assert overview.totals.total == 500
    assert len(overview.sections[0].strip) == 500
    assert documents.list_by_ids_calls <= 1
    assert documents.get_calls == 0
