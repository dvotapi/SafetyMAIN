from __future__ import annotations

from backend.core.domain.entities.shelf_section import ShelfSection
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
from backend.core.domain.value_objects.safety_ids import ShelfSectionId


class InMemoryShelfSectionRepository(ShelfSectionRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[ShelfSectionId, ShelfSection] = {}

    def add(self, section: ShelfSection) -> None:
        for other in self._by_id.values():
            if other.organization_id != section.organization_id:
                continue
            if other.code == section.code:
                raise DuplicateShelfSectionCode(
                    organization_id=section.organization_id, code=section.code
                )
            if other.number == section.number:
                raise DuplicateShelfSectionNumber(
                    organization_id=section.organization_id, number=section.number
                )
        self._by_id[section.id] = section

    def get(
        self, organization_id: OrganizationId, section_id: ShelfSectionId
    ) -> ShelfSection | None:
        section = self._by_id.get(section_id)
        if section is None or section.organization_id != organization_id:
            return None
        return section

    def get_by_code(self, organization_id: OrganizationId, code: str) -> ShelfSection | None:
        for section in self._by_id.values():
            if section.organization_id == organization_id and section.code == code:
                return section
        return None

    def list(self, organization_id: OrganizationId) -> tuple[ShelfSection, ...]:
        items = [s for s in self._by_id.values() if s.organization_id == organization_id]
        items.sort(key=lambda section: section.number)
        return tuple(items)

    def save(self, section: ShelfSection, *, expected_version: int) -> None:
        existing = self.get(section.organization_id, section.id)
        if existing is None:
            raise ShelfSectionNotFound(section.id)
        if existing.version != expected_version:
            raise ShelfSectionVersionConflict(
                section_id=section.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        self._by_id[section.id] = section

    def snapshot(self) -> dict[ShelfSectionId, ShelfSection]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[ShelfSectionId, ShelfSection]) -> None:
        self._by_id = dict(snapshot)
