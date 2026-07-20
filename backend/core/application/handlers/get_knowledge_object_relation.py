from __future__ import annotations

from backend.core.application.handlers.knowledge_object_access import (
    validate_knowledge_object_relation_organization,
)
from backend.core.application.queries.get_knowledge_object_relation import (
    GetKnowledgeObjectRelationQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObjectRelation


class GetKnowledgeObjectRelationHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(
        self,
        query: GetKnowledgeObjectRelationQuery,
    ) -> KnowledgeObjectRelation:
        relation = self._unit_of_work.relations.get(query.relation_id)
        validate_knowledge_object_relation_organization(relation, query.organization_id)
        return relation
