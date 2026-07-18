from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.domain.entities import (
    KnowledgeObject,
    KnowledgeObjectRelation,
    KnowledgeObjectStatus,
)
from backend.core.domain.events import (
    BaseDomainEvent,
    KnowledgeObjectRelationCreated,
    KnowledgeObjectRelationRemoved,
)
from backend.core.domain.exceptions import (
    CrossOrganizationKnowledgeObjectRelation,
    InvalidKnowledgeObjectStateTransition,
    SelfReferencingKnowledgeObjectRelation,
)
from backend.core.domain.value_objects import KnowledgeObjectRelationType


class KnowledgeObjectRelationService:
    def create_relation(
        self,
        *,
        source_object: KnowledgeObject,
        target_object: KnowledgeObject,
        relation_type: KnowledgeObjectRelationType,
    ) -> tuple[KnowledgeObjectRelation, BaseDomainEvent]:
        self._validate_relation_endpoints(source_object, target_object)

        relation = KnowledgeObjectRelation(
            relation_id=uuid4(),
            organization_id=source_object.header.organization_id,
            source_object_id=source_object.header.id,
            target_object_id=target_object.header.id,
            relation_type=relation_type,
            created_at=datetime.now(UTC),
        )
        event = KnowledgeObjectRelationCreated(
            aggregate_id=source_object.header.id,
            payload={
                "relation_id": str(relation.relation_id),
                "source_object_id": str(relation.source_object_id.value),
                "target_object_id": str(relation.target_object_id.value),
                "relation_type": relation.relation_type.value,
            },
        )

        return relation, event

    def remove_relation(
        self,
        relation: KnowledgeObjectRelation,
    ) -> BaseDomainEvent:
        return KnowledgeObjectRelationRemoved(
            aggregate_id=relation.source_object_id,
            payload={
                "relation_id": str(relation.relation_id),
                "source_object_id": str(relation.source_object_id.value),
                "target_object_id": str(relation.target_object_id.value),
                "relation_type": relation.relation_type.value,
            },
        )

    def _validate_relation_endpoints(
        self,
        source_object: KnowledgeObject,
        target_object: KnowledgeObject,
    ) -> None:
        if source_object.header.id == target_object.header.id:
            raise SelfReferencingKnowledgeObjectRelation(source_object.header.id)

        if source_object.header.organization_id != target_object.header.organization_id:
            raise CrossOrganizationKnowledgeObjectRelation(
                source_organization_id=source_object.header.organization_id,
                target_organization_id=target_object.header.organization_id,
            )

        self._ensure_not_deleted(source_object)
        self._ensure_not_deleted(target_object)

    def _ensure_not_deleted(self, knowledge_object: KnowledgeObject) -> None:
        if knowledge_object.header.status is KnowledgeObjectStatus.DELETED:
            raise InvalidKnowledgeObjectStateTransition(
                knowledge_object_id=knowledge_object.header.id,
                current_status=knowledge_object.header.status,
                requested_status=KnowledgeObjectStatus.ACTIVE,
            )
