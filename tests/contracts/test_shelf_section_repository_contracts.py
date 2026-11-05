from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.domain.exceptions.shelf import (
    DuplicateShelfSectionCode,
    DuplicateShelfSectionNumber,
    ShelfSectionNotFound,
    ShelfSectionVersionConflict,
)
from backend.core.domain.repositories.shelf_section_repository import (
    ShelfSectionRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.infrastructure.persistence.in_memory.shelf_section_repository import (
    InMemoryShelfSectionRepository,
)
from tests.fixtures.compliance_documents import FIXED_AT
from tests.fixtures.shelf import make_section


class ShelfSectionRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> ShelfSectionRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_organization_isolation(
        self, repository: ShelfSectionRepositoryContract
    ) -> None:
        section = make_section()
        repository.add(section)

        assert repository.get(section.organization_id, section.id) == section
        assert repository.get_by_code(section.organization_id, "ТрБ") == section
        assert repository.get(OrganizationId(value=uuid4()), section.id) is None
        assert repository.get_by_code(OrganizationId(value=uuid4()), "ТрБ") is None

    def test_code_and_number_are_unique_per_organization(
        self, repository: ShelfSectionRepositoryContract
    ) -> None:
        section = make_section()
        repository.add(section)
        with pytest.raises(DuplicateShelfSectionCode):
            repository.add(
                make_section(organization_id=section.organization_id, number=11, subsections=())
            )
        with pytest.raises(DuplicateShelfSectionNumber):
            repository.add(
                make_section(
                    organization_id=section.organization_id, code="ВМ", subsections=()
                )
            )
        repository.add(make_section())  # same code and number, other organization

    def test_list_orders_by_number(self, repository: ShelfSectionRepositoryContract) -> None:
        organization_id = OrganizationId(value=uuid4())
        fire = make_section(organization_id=organization_id, code="ПожБ", number=8)
        system = make_section(organization_id=organization_id, code="СУ", number=1)
        repository.add(fire)
        repository.add(system)
        repository.add(make_section())

        assert repository.list(organization_id) == (system, fire)

    def test_save_checks_version_and_existence(
        self, repository: ShelfSectionRepositoryContract
    ) -> None:
        section = make_section()
        repository.add(section)
        renamed = section.rename(title="ТрБез", at=FIXED_AT, expected_version=section.version)
        repository.save(renamed, expected_version=section.version)
        assert repository.get(section.organization_id, section.id) == renamed

        stale = renamed.rename(title="Другое", at=FIXED_AT, expected_version=renamed.version)
        with pytest.raises(ShelfSectionVersionConflict):
            repository.save(stale, expected_version=section.version)
        with pytest.raises(ShelfSectionNotFound):
            repository.save(make_section(), expected_version=1)

    def test_subsections_round_trip_in_order(
        self, repository: ShelfSectionRepositoryContract
    ) -> None:
        section = make_section(subsections=(("01", "А"), ("02", "Б"), ("03", "В")))
        repository.add(section)
        extended = section.add_subsection(
            code="ТрБ.04", title="Г", at=FIXED_AT, expected_version=section.version
        )
        repository.save(extended, expected_version=section.version)

        stored = repository.get(section.organization_id, section.id)
        assert stored is not None
        assert [item.code for item in stored.subsections] == [
            "ТрБ.01",
            "ТрБ.02",
            "ТрБ.03",
            "ТрБ.04",
        ]
        assert stored == extended


class TestInMemoryShelfSectionRepository(ShelfSectionRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> ShelfSectionRepositoryContract:
        return InMemoryShelfSectionRepository()
