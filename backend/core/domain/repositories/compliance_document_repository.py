from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_document_query import (
    ComplianceDocumentPage,
    ComplianceDocumentQuery,
)
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId


class ComplianceDocumentRepositoryContract(Protocol):
    """Organization-scoped compliance document persistence contract.

    ``add`` and ``save`` raise ``DuplicateActiveComplianceDocumentCode`` when
    another ``active`` or ``under_review`` document of the organization uses
    the same code (D9). When a new edition supersedes an old one, save the
    superseded edition first.
    """

    def add(self, document: ComplianceDocument) -> None:
        ...

    def get(
        self,
        organization_id: OrganizationId,
        document_id: ComplianceDocumentId,
    ) -> ComplianceDocument | None:
        ...

    def list(self, query: ComplianceDocumentQuery) -> ComplianceDocumentPage:
        """Matching documents, newest first."""
        ...

    def save(self, document: ComplianceDocument, *, expected_version: int) -> None:
        ...
