from __future__ import annotations

from uuid import UUID

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


class KnowledgeObjectRelationError(SafetyMainDomainError):
    """Base class for Knowledge Object Relation domain errors."""


class KnowledgeObjectRelationNotFound(KnowledgeObjectRelationError):
    def __init__(self, relation_id: UUID) -> None:
        self.relation_id = relation_id
        super().__init__(f"Knowledge Object relation was not found: {relation_id}")


class DuplicateKnowledgeObjectRelation(KnowledgeObjectRelationError):
    def __init__(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType,
    ) -> None:
        self.organization_id = organization_id
        self.source_object_id = source_object_id
        self.target_object_id = target_object_id
        self.relation_type = relation_type
        super().__init__(
            "Knowledge Object relation already exists: "
            f"{source_object_id.value} --{relation_type.value}--> "
            f"{target_object_id.value}"
        )


class SelfReferencingKnowledgeObjectRelation(KnowledgeObjectRelationError):
    def __init__(self, knowledge_object_id: KnowledgeObjectId) -> None:
        self.knowledge_object_id = knowledge_object_id
        super().__init__(
            "Knowledge Object relation cannot reference itself: "
            f"{knowledge_object_id.value}"
        )


class CrossOrganizationKnowledgeObjectRelation(KnowledgeObjectRelationError):
    def __init__(
        self,
        source_organization_id: OrganizationId,
        target_organization_id: OrganizationId,
    ) -> None:
        self.source_organization_id = source_organization_id
        self.target_organization_id = target_organization_id
        super().__init__(
            "Knowledge Object relation cannot cross organizations: "
            f"{source_organization_id.value} != {target_organization_id.value}"
        )
