from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.queries.relation_direction import RelationDirection
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


@dataclass(frozen=True, slots=True)
class GetConnectedKnowledgeObjectsQuery:
    organization_id: OrganizationId
    knowledge_object_id: KnowledgeObjectId
    direction: RelationDirection = RelationDirection.OUTGOING
    relation_type: KnowledgeObjectRelationType | None = None
