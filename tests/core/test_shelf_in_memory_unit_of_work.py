from __future__ import annotations

import pytest

from backend.core.domain.value_objects.shelf_enums import SlotExclusionReason
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryShelfSectionRepository,
    InMemoryShelfSlotRepository,
    InMemoryUnitOfWork,
)
from tests.fixtures.compliance_documents import FIXED_AT, make_actor
from tests.fixtures.shelf import make_section, make_slot


def test_shelf_repositories_roll_back_with_the_unit_of_work() -> None:
    sections = InMemoryShelfSectionRepository()
    slots = InMemoryShelfSlotRepository()
    section = make_section()
    slot = make_slot(section)
    sections.add(section)
    slots.add(slot)

    with pytest.raises(RuntimeError), InMemoryUnitOfWork(
        shelf_sections=sections, shelf_slots=slots
    ) as uow:
        uow.shelf_sections.add(
            make_section(organization_id=section.organization_id, code="ВМ", number=5)
        )
        excluded = slot.exclude(
            reason=SlotExclusionReason.OTHER,
            comment="Откатится",
            at=FIXED_AT,
            actor_id=make_actor(),
            expected_version=1,
        )
        uow.shelf_slots.save(excluded, expected_version=1)
        raise RuntimeError("boom")

    assert sections.list(section.organization_id) == (section,)
    assert slots.get(slot.organization_id, slot.id) == slot


def test_shelf_changes_survive_commit() -> None:
    uow = InMemoryUnitOfWork()
    section = make_section()
    with uow:
        uow.shelf_sections.add(section)
        uow.shelf_slots.add(make_slot(section))
        uow.commit()
    assert uow.shelf_sections.get(section.organization_id, section.id) == section
    assert len(uow.shelf_slots.list_all(section.organization_id)) == 1
