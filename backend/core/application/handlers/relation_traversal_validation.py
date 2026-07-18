from __future__ import annotations

from backend.core.domain.entities import KnowledgeObject, KnowledgeObjectStatus
from backend.core.domain.exceptions import (
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectNotFound,
)
from backend.core.domain.value_objects import OrganizationId


def validate_traversal_root(
    knowledge_object: KnowledgeObject,
    organization_id: OrganizationId,
) -> None:
    if knowledge_object.header.organization_id != organization_id:
        raise KnowledgeObjectNotFound(knowledge_object.header.id)

    if knowledge_object.header.status is KnowledgeObjectStatus.DELETED:
        raise InvalidKnowledgeObjectStateTransition(
            knowledge_object_id=knowledge_object.header.id,
            current_status=knowledge_object.header.status,
            requested_status=KnowledgeObjectStatus.ACTIVE,
        )
