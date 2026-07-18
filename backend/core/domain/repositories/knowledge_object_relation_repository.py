from __future__ import annotations

from typing import Protocol, Sequence
from uuid import UUID

from backend.core.domain.entities.knowledge_object_relation import (
    KnowledgeObjectRelation,
)
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


class KnowledgeObjectRelationRepositoryContract(Protocol):
    """Repository contract for directed Knowledge Object relations."""

    def add(self, relation: KnowledgeObjectRelation) -> None:
        ...

    def get(self, relation_id: UUID) -> KnowledgeObjectRelation:
        ...

    def remove(self, relation_id: UUID) -> None:
        ...

    def exists(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType,
    ) -> bool:
        ...

    def outgoing(
        self,
        organization_id: OrganizationId,
        source_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> Sequence[KnowledgeObjectRelation]:
        ...

    def incoming(
        self,
        organization_id: OrganizationId,
        target_object_id: KnowledgeObjectId,
        relation_type: KnowledgeObjectRelationType | None = None,
    ) -> Sequence[KnowledgeObjectRelation]:
        ...
