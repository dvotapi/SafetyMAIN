from __future__ import annotations

from backend.core.application.queries.search_knowledge_objects import (
    SearchKnowledgeObjectsQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects.knowledge_object_search_criteria import (
    KnowledgeObjectSearchCriteria,
)
from backend.core.domain.value_objects.knowledge_object_search_result import (
    KnowledgeObjectSearchResult,
)


class SearchKnowledgeObjectsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: SearchKnowledgeObjectsQuery) -> KnowledgeObjectSearchResult:
        criteria = KnowledgeObjectSearchCriteria(
            organization_id=query.organization_id,
            object_type=query.object_type,
            status=query.status,
            metadata_equals=query.metadata_equals,
            limit=query.limit,
            offset=query.offset,
        )

        return self._unit_of_work.knowledge_objects.search(criteria)
