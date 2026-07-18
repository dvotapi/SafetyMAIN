from __future__ import annotations

from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.infrastructure.persistence.sqlalchemy.models import (
    KnowledgeObjectRelationModel,
)


def relation_to_model(
    relation: KnowledgeObjectRelation,
) -> KnowledgeObjectRelationModel:
    return KnowledgeObjectRelationModel(
        relation_id=relation.relation_id,
        organization_id=relation.organization_id.value,
        source_object_id=relation.source_object_id.value,
        target_object_id=relation.target_object_id.value,
        relation_type=relation.relation_type.value,
        created_at=relation.created_at,
    )


def relation_to_domain(
    model: KnowledgeObjectRelationModel,
) -> KnowledgeObjectRelation:
    return KnowledgeObjectRelation(
        relation_id=model.relation_id,
        organization_id=model.organization_id,
        source_object_id=model.source_object_id,
        target_object_id=model.target_object_id,
        relation_type=model.relation_type,
        created_at=model.created_at,
    )
