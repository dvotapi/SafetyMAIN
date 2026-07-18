from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.domain.entities import KnowledgeObjectRelation
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers import (
    relation_to_domain,
    relation_to_model,
)


def test_relation_mapping_round_trip_preserves_domain_values() -> None:
    relation = KnowledgeObjectRelation(
        relation_id=uuid4(),
        organization_id=OrganizationId(value=uuid4()),
        source_object_id=KnowledgeObjectId(value=uuid4()),
        target_object_id=KnowledgeObjectId(value=uuid4()),
        relation_type=KnowledgeObjectRelationType(value="addresses"),
        created_at=datetime.now(UTC),
    )

    model = relation_to_model(relation)
    mapped_relation = relation_to_domain(model)

    assert mapped_relation == relation
