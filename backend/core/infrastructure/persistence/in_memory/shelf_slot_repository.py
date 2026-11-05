from __future__ import annotations

from collections.abc import Iterable

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
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
)


class InMemoryShelfSlotRepository(ShelfSlotRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[ShelfSlotId, ShelfSlot] = {}

    def add(self, slot: ShelfSlot) -> None:
        if self.get_by_code(slot.organization_id, slot.code.value) is not None:
            raise DuplicateShelfSlotCode(
                organization_id=slot.organization_id, code=slot.code.value
            )
        self._by_id[slot.id] = slot

    def get(self, organization_id: OrganizationId, slot_id: ShelfSlotId) -> ShelfSlot | None:
        slot = self._by_id.get(slot_id)
        if slot is None or slot.organization_id != organization_id:
            return None
        return slot

    def get_by_code(self, organization_id: OrganizationId, code: str) -> ShelfSlot | None:
        for slot in self._by_id.values():
            if slot.organization_id == organization_id and slot.code.value == code:
                return slot
        return None

    def list_by_section(
        self, organization_id: OrganizationId, section_id: ShelfSectionId
    ) -> tuple[ShelfSlot, ...]:
        return self._ordered(
            slot for slot in self._of(organization_id) if slot.section_id == section_id
        )

    def list_all(self, organization_id: OrganizationId) -> tuple[ShelfSlot, ...]:
        return self._ordered(self._of(organization_id))

    def search(
        self, organization_id: OrganizationId, query: str, *, limit: int
    ) -> tuple[ShelfSlot, ...]:
        needle = query.strip().lower()
        if not needle:
            return ()
        matches = self._ordered(
            slot
            for slot in self._of(organization_id)
            if needle in slot.code.value.lower()
            or needle in slot.title.lower()
            or needle in slot.short_title.lower()
        )
        return matches[:limit]

    def list_by_document(
        self, organization_id: OrganizationId, document_id: ComplianceDocumentId
    ) -> tuple[ShelfSlot, ...]:
        return self._ordered(
            slot
            for slot in self._of(organization_id)
            if document_id in slot.linked_document_ids
        )

    def save(self, slot: ShelfSlot, *, expected_version: int) -> None:
        existing = self.get(slot.organization_id, slot.id)
        if existing is None:
            raise ShelfSlotNotFound(slot.id)
        if existing.version != expected_version:
            raise ShelfSlotVersionConflict(
                slot_id=slot.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        self._by_id[slot.id] = slot

    def snapshot(self) -> dict[ShelfSlotId, ShelfSlot]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[ShelfSlotId, ShelfSlot]) -> None:
        self._by_id = dict(snapshot)

    def _of(self, organization_id: OrganizationId) -> list[ShelfSlot]:
        return [s for s in self._by_id.values() if s.organization_id == organization_id]

    @staticmethod
    def _ordered(slots: Iterable[ShelfSlot]) -> tuple[ShelfSlot, ...]:
        return tuple(sorted(slots, key=lambda slot: slot.code.value))
