from __future__ import annotations

from backend.core.application.queries.compliance_documents import (
    ListDocumentTypesQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.document_type import DocumentType


class ListDocumentTypesHandler:
    """Return organization-scoped document types.

    Reads are not audited (Risk Control precedent).
    """

    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListDocumentTypesQuery) -> tuple[DocumentType, ...]:
        return self._unit_of_work.document_types.list(
            query.organization_id,
            include_inactive=query.include_inactive,
        )
