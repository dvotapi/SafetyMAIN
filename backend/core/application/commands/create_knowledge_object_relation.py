from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
)


@dataclass(frozen=True, slots=True)
class CreateKnowledgeObjectRelationCommand:
    source_object_id: KnowledgeObjectId
    target_object_id: KnowledgeObjectId
    relation_type: KnowledgeObjectRelationType
