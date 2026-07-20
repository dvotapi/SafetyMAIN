from __future__ import annotations

from backend.api.schemas.relations import KnowledgeObjectRelationResponse
from backend.core.domain.entities import KnowledgeObjectRelation


def to_relation_response(
    relation: KnowledgeObjectRelation,
) -> KnowledgeObjectRelationResponse:
    return KnowledgeObjectRelationResponse(
        id=relation.relation_id,
        organization_id=relation.organization_id.value,
        source_object_id=relation.source_object_id.value,
        target_object_id=relation.target_object_id.value,
        type=relation.relation_type.value,
        created_at=relation.created_at,
    )


def to_relation_responses(
    relations: tuple[KnowledgeObjectRelation, ...] | list[KnowledgeObjectRelation],
) -> tuple[KnowledgeObjectRelationResponse, ...]:
    return tuple(to_relation_response(relation) for relation in relations)
