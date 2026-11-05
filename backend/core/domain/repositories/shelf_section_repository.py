from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import ShelfSectionId


class ShelfSectionRepositoryContract(Protocol):
    """Organization-scoped shelf sections with their subsections; never deleted."""

    def add(self, section: ShelfSection) -> None:
        """Raises ``DuplicateShelfSectionCode`` / ``DuplicateShelfSectionNumber``."""
        ...

    def get(
        self, organization_id: OrganizationId, section_id: ShelfSectionId
    ) -> ShelfSection | None:
        ...

    def get_by_code(self, organization_id: OrganizationId, code: str) -> ShelfSection | None:
        ...

    def list(self, organization_id: OrganizationId) -> tuple[ShelfSection, ...]:
        """Sections of the organization ordered by number."""
        ...

    def save(self, section: ShelfSection, *, expected_version: int) -> None:
        """Raises ``ShelfSectionNotFound`` or ``ShelfSectionVersionConflict``."""
        ...
