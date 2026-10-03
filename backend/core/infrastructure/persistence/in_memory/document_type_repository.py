from __future__ import annotations

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import DuplicateDocumentTypeCode
from backend.core.domain.repositories.document_type_repository import (
    DocumentTypeRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import DocumentTypeId


class InMemoryDocumentTypeRepository(DocumentTypeRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[DocumentTypeId, DocumentType] = {}

    def add(self, document_type: DocumentType) -> None:
        if self.get_by_code(document_type.organization_id, document_type.code) is not None:
            raise DuplicateDocumentTypeCode(
                organization_id=document_type.organization_id,
                code=document_type.code,
            )
        self._by_id[document_type.id] = document_type

    def get(
        self,
        organization_id: OrganizationId,
        document_type_id: DocumentTypeId,
    ) -> DocumentType | None:
        document_type = self._by_id.get(document_type_id)
        if document_type is None or document_type.organization_id != organization_id:
            return None
        return document_type

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: str,
    ) -> DocumentType | None:
        for document_type in self._by_id.values():
            if (
                document_type.organization_id == organization_id
                and document_type.code == code
            ):
                return document_type
        return None

    def list(
        self,
        organization_id: OrganizationId,
        *,
        include_inactive: bool = False,
    ) -> tuple[DocumentType, ...]:
        items = [
            item
            for item in self._by_id.values()
            if item.organization_id == organization_id
            and (include_inactive or item.is_active)
        ]
        items.sort(key=lambda item: item.code)
        return tuple(items)

    def snapshot(self) -> dict[DocumentTypeId, DocumentType]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[DocumentTypeId, DocumentType]) -> None:
        self._by_id = dict(snapshot)
