from __future__ import annotations

from backend.core.domain.entities.compliance_document import (
    ComplianceDocument,
    is_in_force,
)
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentNotFound,
    ComplianceDocumentVersionConflict,
    DuplicateActiveComplianceDocumentCode,
)
from backend.core.domain.repositories.compliance_document_repository import (
    ComplianceDocumentRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_document_query import (
    ComplianceDocumentPage,
    ComplianceDocumentQuery,
)
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId


class InMemoryComplianceDocumentRepository(ComplianceDocumentRepositoryContract):
    def __init__(self) -> None:
        self._by_id: dict[ComplianceDocumentId, ComplianceDocument] = {}

    def add(self, document: ComplianceDocument) -> None:
        self._assert_code_free(document)
        self._by_id[document.id] = document

    def get(
        self,
        organization_id: OrganizationId,
        document_id: ComplianceDocumentId,
    ) -> ComplianceDocument | None:
        document = self._by_id.get(document_id)
        if document is None or document.organization_id != organization_id:
            return None
        return document

    def list(self, query: ComplianceDocumentQuery) -> ComplianceDocumentPage:
        items = [
            item
            for item in self._by_id.values()
            if item.organization_id == query.organization_id
        ]
        if not query.include_archived:
            items = [
                item
                for item in items
                if item.status is not ComplianceDocumentStatus.ARCHIVED
            ]
        if query.document_type_ids is not None:
            items = [
                item for item in items if item.document_type_id in query.document_type_ids
            ]
        if query.status is not None:
            items = [item for item in items if item.status is query.status]
        if query.subject_kind is not None:
            items = [item for item in items if item.subject_kind is query.subject_kind]
        if query.search is not None and query.search.strip():
            needle = query.search.strip().lower()
            items = [
                item
                for item in items
                if needle in item.code.lower() or needle in item.title.lower()
            ]
        if query.review_due is not None:
            review_due = query.review_due
            items = [
                item
                for item in items
                if item.document_type_id in review_due.document_types
                and item.is_review_due(
                    as_of=review_due.as_of,
                    document_type=review_due.document_types[item.document_type_id],
                )
            ]
        items.sort(key=lambda item: (item.created_at, item.id.value), reverse=True)
        return ComplianceDocumentPage(
            items=tuple(items[query.offset : query.offset + query.limit]),
            total=len(items),
            offset=query.offset,
            limit=query.limit,
        )

    def save(self, document: ComplianceDocument, *, expected_version: int) -> None:
        existing = self.get(document.organization_id, document.id)
        if existing is None:
            raise ComplianceDocumentNotFound(document.id)
        if existing.version != expected_version:
            raise ComplianceDocumentVersionConflict(
                document_id=document.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        self._assert_code_free(document)
        self._by_id[document.id] = document

    def snapshot(self) -> dict[ComplianceDocumentId, ComplianceDocument]:
        return dict(self._by_id)

    def restore(self, snapshot: dict[ComplianceDocumentId, ComplianceDocument]) -> None:
        self._by_id = dict(snapshot)

    def _assert_code_free(self, document: ComplianceDocument) -> None:
        if not is_in_force(document.status):
            return
        for other in self._by_id.values():
            if (
                other.id != document.id
                and other.organization_id == document.organization_id
                and other.code == document.code
                and is_in_force(other.status)
            ):
                raise DuplicateActiveComplianceDocumentCode(
                    organization_id=document.organization_id,
                    code=document.code,
                )
