from __future__ import annotations

from typing import Protocol, Sequence

from backend.core.domain.entities.knowledge_object import KnowledgeObject
from backend.core.domain.value_objects import KnowledgeObjectId
from backend.core.domain.value_objects.knowledge_object_search_criteria import (
    KnowledgeObjectSearchCriteria,
)
from backend.core.domain.value_objects.knowledge_object_search_result import (
    KnowledgeObjectSearchResult,
)


class KnowledgeObjectRepositoryContract(Protocol):
    """Repository contract for Knowledge Objects."""

    def add(self, knowledge_object: KnowledgeObject) -> None:
        ...

    def get(self, object_id: KnowledgeObjectId) -> KnowledgeObject:
        ...

    def update(self, knowledge_object: KnowledgeObject) -> None:
        ...

    def history(self, object_id: KnowledgeObjectId) -> Sequence[KnowledgeObject]:
        ...

    def search(
        self,
        criteria: KnowledgeObjectSearchCriteria,
    ) -> KnowledgeObjectSearchResult:
        ...
