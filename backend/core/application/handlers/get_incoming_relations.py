from __future__ import annotations

from typing import Sequence

from backend.core.application.handlers.relation_traversal_validation import (
    validate_traversal_root,
)
from backend.core.application.queries.get_incoming_relations import (
    GetIncomingRelationsQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObjectRelation


class GetIncomingRelationsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(
        self,
        query: GetIncomingRelationsQuery,
    ) -> Sequence[KnowledgeObjectRelation]:
        root_object = self._unit_of_work.knowledge_objects.get(query.knowledge_object_id)
        validate_traversal_root(root_object, query.organization_id)

        return self._unit_of_work.relations.incoming(
            organization_id=query.organization_id,
            target_object_id=query.knowledge_object_id,
            relation_type=query.relation_type,
        )
