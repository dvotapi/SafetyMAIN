from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


@dataclass(frozen=True, slots=True)
class GetOutgoingRelationsQuery:
    organization_id: OrganizationId
    knowledge_object_id: KnowledgeObjectId
    relation_type: KnowledgeObjectRelationType | None = None
