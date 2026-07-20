from __future__ import annotations

from collections.abc import Sequence

from backend.core.application.handlers.knowledge_object_access import (
    validate_knowledge_object_organization,
)
from backend.core.application.queries.get_knowledge_object_history import (
    GetKnowledgeObjectHistoryQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.knowledge_object import KnowledgeObject


class GetKnowledgeObjectHistoryHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(
        self,
        query: GetKnowledgeObjectHistoryQuery,
    ) -> Sequence[KnowledgeObject]:
        current_object = self._unit_of_work.knowledge_objects.get(query.object_id)
        validate_knowledge_object_organization(current_object, query.organization_id)
        return self._unit_of_work.knowledge_objects.history(query.object_id)
