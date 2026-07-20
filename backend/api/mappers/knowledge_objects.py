from __future__ import annotations

from backend.api.schemas.knowledge_objects import KnowledgeObjectResponse
from backend.core.domain.entities.knowledge_object import KnowledgeObject


def to_knowledge_object_response(
    knowledge_object: KnowledgeObject,
) -> KnowledgeObjectResponse:
    return KnowledgeObjectResponse(
        id=knowledge_object.header.id.value,
        organization_id=knowledge_object.header.organization_id.value,
        type=knowledge_object.header.object_type.value,
        status=knowledge_object.header.status.value.lower(),
        version=knowledge_object.header.version.value,
        metadata=dict(knowledge_object.payload),
        created_at=knowledge_object.header.created_at,
        updated_at=knowledge_object.header.updated_at,
    )


def to_knowledge_object_responses(
    knowledge_objects: tuple[KnowledgeObject, ...] | list[KnowledgeObject],
) -> tuple[KnowledgeObjectResponse, ...]:
    return tuple(to_knowledge_object_response(item) for item in knowledge_objects)
