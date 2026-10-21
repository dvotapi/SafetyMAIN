from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.queries.compliance_documents import (
    GetComplianceDocumentQuery,
    ListComplianceDocumentsQuery,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentNotFound,
    DocumentTypeNotFound,
)
from backend.core.domain.value_objects.compliance_document_query import (
    ComplianceDocumentPage,
    ComplianceDocumentQuery,
    ComplianceDocumentReviewDueFilter,
)
from backend.core.domain.value_objects.safety_ids import DocumentTypeId


@dataclass(frozen=True, slots=True)
class ComplianceDocumentWithContext:
    """Document plus its resolved type and backend-computed ``is_review_due``.

    The handler shapes this so the API mapper has everything it needs without
    reaching into the repositories. ``document_type`` may be ``None`` when the
    resulting document is not in force and ``is_review_due`` is trivially
    false (lifecycle handlers skip the catalog fetch in that case).
    """

    document: ComplianceDocument
    document_type: DocumentType | None
    is_review_due: bool


@dataclass(frozen=True, slots=True)
class ComplianceDocumentPageWithContext:
    items: tuple[ComplianceDocumentWithContext, ...]
    total: int
    offset: int
    limit: int


class GetComplianceDocumentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(
        self, query: GetComplianceDocumentQuery
    ) -> ComplianceDocumentWithContext:
        document = self._unit_of_work.compliance_documents.get(
            query.organization_id,
            query.document_id,
        )
        if document is None:
            raise ComplianceDocumentNotFound(query.document_id)
        document_type = self._unit_of_work.document_types.get(
            document.organization_id,
            document.document_type_id,
        )
        if document_type is None:
            raise DocumentTypeNotFound(document.document_type_id)
        today = self._clock.now().date()
        return ComplianceDocumentWithContext(
            document=document,
            document_type=document_type,
            is_review_due=document.is_review_due(
                as_of=today, document_type=document_type
            ),
        )


class ListComplianceDocumentsHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(
        self, query: ListComplianceDocumentsQuery
    ) -> ComplianceDocumentPageWithContext:
        today = self._clock.now().date()
        # The ``review_due`` filter needs the type of every document the other
        # criteria keep (including inactive types), so load the map up front.
        type_map: dict[DocumentTypeId, DocumentType] = {
            document_type.id: document_type
            for document_type in self._unit_of_work.document_types.list(
                query.organization_id,
                include_inactive=True,
            )
        }
        review_due_filter: ComplianceDocumentReviewDueFilter | None = None
        if query.review_due is True:
            review_due_filter = ComplianceDocumentReviewDueFilter(
                as_of=today, document_types=type_map
            )
        type_id_filter: frozenset[DocumentTypeId] | None = (
            frozenset(query.document_type_ids) if query.document_type_ids else None
        )
        if query.safety_domain is not None:
            # Resolve the safety domain through the type map here so the domain
            # repository stays unaware of DocumentType.
            domain_ids = frozenset(
                type_id
                for type_id, document_type in type_map.items()
                if document_type.safety_domain is query.safety_domain
            )
            type_id_filter = (
                domain_ids
                if type_id_filter is None
                else type_id_filter & domain_ids
            )
            if not type_id_filter:
                return ComplianceDocumentPageWithContext(
                    items=(), total=0, offset=query.offset, limit=query.limit
                )
        page: ComplianceDocumentPage = self._unit_of_work.compliance_documents.list(
            ComplianceDocumentQuery(
                organization_id=query.organization_id,
                document_type_ids=type_id_filter,
                status=query.status,
                subject_kind=query.subject_kind,
                review_due=review_due_filter,
                include_archived=query.include_archived,
                search=query.search,
                offset=query.offset,
                limit=query.limit,
            )
        )
        items: list[ComplianceDocumentWithContext] = []
        for document in page.items:
            document_type = type_map.get(document.document_type_id)
            if document_type is None:
                raise DocumentTypeNotFound(document.document_type_id)
            is_due = document.is_review_due(
                as_of=today, document_type=document_type
            )
            items.append(
                ComplianceDocumentWithContext(
                    document=document,
                    document_type=document_type,
                    is_review_due=is_due,
                )
            )
        return ComplianceDocumentPageWithContext(
            items=tuple(items),
            total=page.total,
            offset=page.offset,
            limit=page.limit,
        )
