from __future__ import annotations

from typing import Sequence

from backend.core.application.handlers.relation_traversal_validation import (
    validate_traversal_root,
)
from backend.core.application.queries.get_connected_knowledge_objects import (
    GetConnectedKnowledgeObjectsQuery,
)
from backend.core.application.queries.relation_direction import RelationDirection
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObject, KnowledgeObjectStatus
from backend.core.domain.exceptions import KnowledgeObjectNotFound
from backend.core.domain.value_objects import KnowledgeObjectId, OrganizationId


class GetConnectedKnowledgeObjectsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(
        self,
        query: GetConnectedKnowledgeObjectsQuery,
    ) -> Sequence[KnowledgeObject]:
        root_object = self._unit_of_work.knowledge_objects.get(query.knowledge_object_id)
        validate_traversal_root(root_object, query.organization_id)

        connected_ids = self._get_connected_ids(query)
        connected_objects = [
            knowledge_object
            for knowledge_object in (
                self._get_available_object(object_id, query.organization_id)
                for object_id in connected_ids
            )
            if knowledge_object is not None
        ]

        return tuple(
            sorted(
                connected_objects,
                key=lambda knowledge_object: str(knowledge_object.header.id.value),
            )
        )

    def _get_connected_ids(
        self,
        query: GetConnectedKnowledgeObjectsQuery,
    ) -> tuple[KnowledgeObjectId, ...]:
        connected_ids: dict[KnowledgeObjectId, None] = {}

        if query.direction in (RelationDirection.OUTGOING, RelationDirection.BOTH):
            for relation in self._unit_of_work.relations.outgoing(
                organization_id=query.organization_id,
                source_object_id=query.knowledge_object_id,
                relation_type=query.relation_type,
            ):
                connected_ids.setdefault(relation.target_object_id, None)

        if query.direction in (RelationDirection.INCOMING, RelationDirection.BOTH):
            for relation in self._unit_of_work.relations.incoming(
                organization_id=query.organization_id,
                target_object_id=query.knowledge_object_id,
                relation_type=query.relation_type,
            ):
                connected_ids.setdefault(relation.source_object_id, None)

        return tuple(connected_ids)

    def _get_available_object(
        self,
        object_id: KnowledgeObjectId,
        organization_id: OrganizationId,
    ) -> KnowledgeObject | None:
        try:
            knowledge_object = self._unit_of_work.knowledge_objects.get(object_id)
        except KnowledgeObjectNotFound:
            return None

        if knowledge_object.header.organization_id != organization_id:
            return None

        if knowledge_object.header.status is KnowledgeObjectStatus.DELETED:
            return None

        return knowledge_object
