from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.exceptions.shelf import (
    DuplicateShelfSlotCode,
    ShelfSlotNotFound,
    ShelfSlotVersionConflict,
)
from backend.core.domain.repositories.shelf_slot_repository import (
    ShelfSlotRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    LegalBasisConfidence,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_values import SlotLegalBasis
from backend.core.infrastructure.persistence.in_memory.shelf_slot_repository import (
    InMemoryShelfSlotRepository,
)
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    compliance_document_draft,
    make_actor,
    make_document_type,
)
from tests.fixtures.shelf import make_section, make_slot

LATER = FIXED_AT + timedelta(hours=2)


def rich_slot(section: ShelfSection) -> ShelfSlot:
    return ShelfSlot.create(
        organization_id=section.organization_id,
        section=section,
        code=f"{section.subsections[1].code}.07",
        title="Оценка уязвимости объекта транспортной инфраструктуры",
        short_title="Оценка уязвимости ОТИ",
        document_kind="Акт",
        kept_on=SlotKeptOn.FACILITY,
        obligation_level=SlotObligationLevel.CONDITIONAL,
        applicability_condition="Есть категорированный ОТИ",
        legal_basis=SlotLegalBasis(
            regulation="16-ФЗ",
            clause="ст. 5",
            quote="Оценка уязвимости проводится…",
            source_url="https://example.org/16-fz",
            confidence=LegalBasisConfidence.VERIFIED,
        ),
        review_cycle_text="при изменениях",
        review_period_months=36,
        curated_status=CuratedSlotStatus.TO_CLARIFY,
        document_type_code="transport_vulnerability",
        proposed_document_type="Акт оценки уязвимости (новый)",
        responsible_text="Ответственный за ТБ",
        legacy_location="Папка 10",
        notes="Проверить категорию",
        package_code="ПК-10",
        legacy_code="10.2.7",
        created_by=make_actor(),
        created_at=FIXED_AT,
    )


class ShelfSlotRepositoryContractSuite:
    """Persistence contract; implementations may need seeded sections, users, documents."""

    @pytest.fixture()
    def repository(self) -> ShelfSlotRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_organization_isolation(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        slot = make_slot()
        repository.add(slot)

        assert repository.get(slot.organization_id, slot.id) == slot
        assert repository.get_by_code(slot.organization_id, slot.code.value) == slot
        assert repository.get(OrganizationId(value=uuid4()), slot.id) is None
        assert repository.get_by_code(OrganizationId(value=uuid4()), slot.code.value) is None

    def test_round_trip_preserves_all_fields(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        slot = rich_slot(make_section())
        repository.add(slot)
        assert repository.get(slot.organization_id, slot.id) == slot

        excluded = slot.exclude(
            reason=SlotExclusionReason.CONDITION_NOT_MET,
            comment="Нет категорированных ОТИ",
            at=LATER,
            actor_id=make_actor(),
            expected_version=1,
        )
        repository.save(excluded, expected_version=1)
        assert repository.get(slot.organization_id, slot.id) == excluded

    def test_code_is_unique_per_organization_including_excluded(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        section = make_section()
        slot = make_slot(section).exclude(
            reason=SlotExclusionReason.DUPLICATE,
            comment="Дублирует другое место",
            at=FIXED_AT,
            actor_id=make_actor(),
            expected_version=1,
        )
        repository.add(slot)
        with pytest.raises(DuplicateShelfSlotCode):
            repository.add(make_slot(section, code=slot.code.value))
        repository.add(make_slot(code=slot.code.value))  # other organization

    def test_lists_are_scoped_and_ordered_by_code(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        section = make_section()
        other_section = make_section(
            organization_id=section.organization_id, code="ВМ", number=5
        )
        later = make_slot(section, code="ТрБ.02.01")
        first = make_slot(section, code="ТрБ.01.02")
        second = make_slot(section, code="ТрБ.01.10")
        explosive = make_slot(other_section, code="ВМ.01.01")
        for slot in (later, explosive, second, first, make_slot()):
            repository.add(slot)

        assert repository.list_by_section(section.organization_id, section.id) == (
            first,
            second,
            later,
        )
        assert repository.list_all(section.organization_id) == (
            explosive,
            first,
            second,
            later,
        )

    def test_search_matches_code_title_and_short_title(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        section = make_section()
        by_code = make_slot(section, code="ТрБ.01.05", title="Приказ", short_title="Приказ")
        by_title = make_slot(
            section,
            code="ТрБ.02.01",
            title="План обеспечения транспортной безопасности",
            short_title="План",
        )
        by_short = make_slot(
            section, code="ТрБ.02.02", title="Перечень", short_title="Перечень ТРАНСПОРТНЫХ"
        )
        with_wildcards = make_slot(
            section, code="ТрБ.02.03", title="Доля 100% _ \\", short_title="Доля"
        )
        for slot in (by_code, by_title, by_short, with_wildcards, make_slot()):
            repository.add(slot)
        organization_id = section.organization_id

        assert repository.search(organization_id, "трб.01", limit=10) == (by_code,)
        assert repository.search(organization_id, "Транспортн", limit=10) == (
            by_title,
            by_short,
        )
        assert repository.search(organization_id, "транспортн", limit=1) == (by_title,)
        assert repository.search(organization_id, "100%", limit=10) == (with_wildcards,)
        assert repository.search(organization_id, "_", limit=10) == (with_wildcards,)
        assert repository.search(organization_id, "\\", limit=10) == (with_wildcards,)
        assert repository.search(organization_id, "%", limit=10) == (with_wildcards,)
        assert repository.search(organization_id, "  ", limit=10) == ()

    def test_links_round_trip_in_order_and_list_by_document(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        section = make_section()
        slot = make_slot(section)
        other = make_slot(section, code="ТрБ.01.02")
        repository.add(slot)
        repository.add(other)
        document_type = make_document_type(organization_id=slot.organization_id)
        current = compliance_document_draft(document_type).model_copy(
            update={"status": ComplianceDocumentStatus.ACTIVE}
        )
        previous = compliance_document_draft(document_type, code="ИОТ-011").model_copy(
            update={"status": ComplianceDocumentStatus.SUPERSEDED}
        )
        actor = make_actor()
        linked = slot.link_document(
            document=current, linked_documents=(), at=LATER, actor_id=actor, expected_version=1
        ).link_document(
            document=previous,
            linked_documents=(current,),
            at=LATER,
            actor_id=actor,
            expected_version=2,
        )
        repository.save(linked, expected_version=1)

        stored = repository.get(slot.organization_id, slot.id)
        assert stored is not None
        assert stored.linked_document_ids == (current.id, previous.id)
        assert repository.list_by_document(slot.organization_id, current.id) == (stored,)
        assert repository.list_by_document(OrganizationId(value=uuid4()), current.id) == ()

        unlinked = stored.unlink_document(
            document_id=current.id, at=LATER, actor_id=actor, expected_version=stored.version
        )
        repository.save(unlinked, expected_version=stored.version)
        assert repository.list_by_document(slot.organization_id, current.id) == ()
        assert repository.list_by_document(
            slot.organization_id, ComplianceDocumentId(value=uuid4())
        ) == ()

    def test_save_checks_version_and_existence(
        self, repository: ShelfSlotRepositoryContract
    ) -> None:
        slot = make_slot(curated_status=CuratedSlotStatus.TO_CLARIFY)
        repository.add(slot)
        actor = make_actor()
        confirmed = slot.confirm_applicable(at=LATER, actor_id=actor, expected_version=1)
        repository.save(confirmed, expected_version=1)

        stale = confirmed.update_details(
            at=LATER, actor_id=actor, expected_version=2, notes="Заметка"
        )
        with pytest.raises(ShelfSlotVersionConflict):
            repository.save(stale, expected_version=1)
        with pytest.raises(ShelfSlotNotFound):
            repository.save(make_slot(), expected_version=1)


class TestInMemoryShelfSlotRepository(ShelfSlotRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> ShelfSlotRepositoryContract:
        return InMemoryShelfSlotRepository()
