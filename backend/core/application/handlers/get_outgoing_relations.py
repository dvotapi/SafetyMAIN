from __future__ import annotations

from typing import Sequence

from backend.core.application.handlers.relation_traversal_validation import (
    validate_traversal_root,
)
from backend.core.application.queries.get_outgoing_relations import (
    GetOutgoingRelationsQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObjectRelation


class GetOutgoingRelationsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(
        self,
        query: GetOutgoingRelationsQuery,
    ) -> Sequence[KnowledgeObjectRelation]:
        root_object = self._unit_of_work.knowledge_objects.get(query.knowledge_object_id)
        validate_traversal_root(root_object, query.organization_id)

        return self._unit_of_work.relations.outgoing(
            organization_id=query.organization_id,
            source_object_id=query.knowledge_object_id,
            relation_type=query.relation_type,
        )
