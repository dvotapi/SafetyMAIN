from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


@dataclass(frozen=True, slots=True)
class CreateKnowledgeObjectRelationCommand:
    organization_id: OrganizationId
    source_object_id: KnowledgeObjectId
    target_object_id: KnowledgeObjectId
    relation_type: KnowledgeObjectRelationType
