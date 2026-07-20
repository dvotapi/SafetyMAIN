from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.api.mappers.relations import to_relation_response
from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


def test_relation_mapper_serializes_all_fields() -> None:
    created_at = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
    relation = KnowledgeObjectRelation(
        relation_id=uuid4(),
        organization_id=OrganizationId(value=uuid4()),
        source_object_id=KnowledgeObjectId(value=uuid4()),
        target_object_id=KnowledgeObjectId(value=uuid4()),
        relation_type=KnowledgeObjectRelationType(value="References"),
        created_at=created_at,
    )

    response = to_relation_response(relation)

    assert response.id == relation.relation_id
    assert response.organization_id == relation.organization_id.value
    assert response.source_object_id == relation.source_object_id.value
    assert response.target_object_id == relation.target_object_id.value
    assert response.type == "references"
    assert response.created_at == created_at
