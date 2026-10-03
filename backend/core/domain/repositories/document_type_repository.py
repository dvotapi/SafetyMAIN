from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import DocumentTypeId


class DocumentTypeRepositoryContract(Protocol):
    """Organization-scoped document type catalog persistence contract."""

    def add(self, document_type: DocumentType) -> None:
        ...

    def get(
        self,
        organization_id: OrganizationId,
        document_type_id: DocumentTypeId,
    ) -> DocumentType | None:
        ...

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: str,
    ) -> DocumentType | None:
        ...

    def list(
        self,
        organization_id: OrganizationId,
        *,
        include_inactive: bool = False,
    ) -> tuple[DocumentType, ...]:
        """Types of the organization ordered by code."""
        ...
