from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.api.mappers.knowledge_objects import to_knowledge_object_response
from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)


def test_mapper_serializes_knowledge_object_fields() -> None:
    now = datetime(2026, 7, 19, 10, 0, tzinfo=UTC)
    knowledge_object = KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Policy",
            organization_id=uuid4(),
            status=KnowledgeObjectStatus.ACTIVE,
            version=2,
            created_at=now,
            updated_at=now,
        ),
        payload={"title": "Policy", "enabled": True, "count": 3},
    )

    response = to_knowledge_object_response(knowledge_object)

    assert response.id == knowledge_object.header.id.value
    assert response.organization_id == knowledge_object.header.organization_id.value
    assert response.type == "policy"
    assert response.status == "active"
    assert response.version == 2
    assert response.metadata == {"title": "Policy", "enabled": True, "count": 3}
    assert response.created_at == now
    assert response.updated_at == now
