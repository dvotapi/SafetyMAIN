from __future__ import annotations

from backend.core.domain.entities import KnowledgeObject, KnowledgeObjectRelation
from backend.core.domain.exceptions import (
    KnowledgeObjectNotFound,
    KnowledgeObjectRelationNotFound,
)
from backend.core.domain.value_objects import OrganizationId


def validate_knowledge_object_organization(
    knowledge_object: KnowledgeObject,
    organization_id: OrganizationId,
) -> None:
    """Ensure the object belongs to the requested organization.

    Cross-organization access is reported as ``KnowledgeObjectNotFound`` so
    callers cannot distinguish missing objects from foreign-organization objects.
    """

    if knowledge_object.header.organization_id != organization_id:
        raise KnowledgeObjectNotFound(knowledge_object.header.id)


def validate_knowledge_object_relation_organization(
    relation: KnowledgeObjectRelation,
    organization_id: OrganizationId,
) -> None:
    if relation.organization_id != organization_id:
        raise KnowledgeObjectRelationNotFound(relation.relation_id)
