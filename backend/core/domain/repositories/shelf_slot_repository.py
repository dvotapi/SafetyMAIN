from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
)


class ShelfSlotRepositoryContract(Protocol):
    """Organization-scoped shelf places; never deleted.

    Lists are ordered by code (code point order), which within a section is
    subsection then place number.
    """

    def add(self, slot: ShelfSlot) -> None:
        """Raises ``DuplicateShelfSlotCode`` (excluded places included)."""
        ...

    def get(self, organization_id: OrganizationId, slot_id: ShelfSlotId) -> ShelfSlot | None:
        ...

    def get_by_code(self, organization_id: OrganizationId, code: str) -> ShelfSlot | None:
        ...

    def list_by_section(
        self, organization_id: OrganizationId, section_id: ShelfSectionId
    ) -> tuple[ShelfSlot, ...]:
        ...

    def list_all(self, organization_id: OrganizationId) -> tuple[ShelfSlot, ...]:
        ...

    def search(
        self, organization_id: OrganizationId, query: str, *, limit: int
    ) -> tuple[ShelfSlot, ...]:
        """Case-insensitive substring match on code, title, or short title."""
        ...

    def list_by_document(
        self, organization_id: OrganizationId, document_id: ComplianceDocumentId
    ) -> tuple[ShelfSlot, ...]:
        """Places the document is linked to."""
        ...

    def save(self, slot: ShelfSlot, *, expected_version: int) -> None:
        """Raises ``ShelfSlotNotFound`` or ``ShelfSlotVersionConflict``."""
        ...
