from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.events import (
    BaseDomainEvent,
    KnowledgeObjectArchived,
    KnowledgeObjectDeleted,
    KnowledgeObjectRestored,
    KnowledgeObjectUpdated,
)
from backend.core.domain.exceptions import (
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectAlreadyActive,
    KnowledgeObjectAlreadyArchived,
    KnowledgeObjectAlreadyDeleted,
)
from backend.core.domain.value_objects import KnowledgeObjectVersion


class KnowledgeObjectService:
    def delete(
        self,
        knowledge_object: KnowledgeObject,
    ) -> tuple[KnowledgeObject, BaseDomainEvent]:
        if knowledge_object.header.status is KnowledgeObjectStatus.DELETED:
            raise KnowledgeObjectAlreadyDeleted(knowledge_object.header.id)

        return self.create_next_version(
            knowledge_object,
            status=KnowledgeObjectStatus.DELETED,
        )

    def archive(
        self,
        knowledge_object: KnowledgeObject,
    ) -> tuple[KnowledgeObject, BaseDomainEvent]:
        if knowledge_object.header.status is KnowledgeObjectStatus.ARCHIVED:
            raise KnowledgeObjectAlreadyArchived(knowledge_object.header.id)

        return self.create_next_version(
            knowledge_object,
            status=KnowledgeObjectStatus.ARCHIVED,
        )

    def restore(
        self,
        knowledge_object: KnowledgeObject,
    ) -> tuple[KnowledgeObject, BaseDomainEvent]:
        if knowledge_object.header.status is KnowledgeObjectStatus.ACTIVE:
            raise KnowledgeObjectAlreadyActive(knowledge_object.header.id)

        return self.create_next_version(
            knowledge_object,
            status=KnowledgeObjectStatus.ACTIVE,
        )

    def create_next_version(
        self,
        knowledge_object: KnowledgeObject,
        *,
        status: KnowledgeObjectStatus,
        payload: dict[str, Any] | None = None,
    ) -> tuple[KnowledgeObject, BaseDomainEvent]:
        self._ensure_transition_allowed(knowledge_object, status)

        next_object = KnowledgeObject(
            header=KnowledgeObjectHeader(
                id=knowledge_object.header.id,
                object_type=knowledge_object.header.object_type,
                organization_id=knowledge_object.header.organization_id,
                status=status,
                version=KnowledgeObjectVersion(
                    value=knowledge_object.header.version.value + 1
                ),
                created_at=knowledge_object.header.created_at,
                updated_at=datetime.now(UTC),
            ),
            payload=dict(knowledge_object.payload if payload is None else payload),
        )

        return next_object, self._create_version_event(knowledge_object, next_object)

    def _ensure_transition_allowed(
        self,
        knowledge_object: KnowledgeObject,
        requested_status: KnowledgeObjectStatus,
    ) -> None:
        if (
            knowledge_object.header.status is KnowledgeObjectStatus.DELETED
            and requested_status is not KnowledgeObjectStatus.DELETED
        ):
            raise InvalidKnowledgeObjectStateTransition(
                knowledge_object_id=knowledge_object.header.id,
                current_status=knowledge_object.header.status,
                requested_status=requested_status,
            )

    def _create_version_event(
        self,
        previous_object: KnowledgeObject,
        next_object: KnowledgeObject,
    ) -> BaseDomainEvent:
        event_payload = {
            "previous_version": previous_object.header.version.value,
            "current_version": next_object.header.version.value,
            "previous_status": previous_object.header.status.value,
            "current_status": next_object.header.status.value,
        }

        if next_object.header.status is KnowledgeObjectStatus.ARCHIVED:
            return KnowledgeObjectArchived(
                aggregate_id=next_object.header.id,
                payload=event_payload,
            )

        if (
            previous_object.header.status is KnowledgeObjectStatus.ARCHIVED
            and next_object.header.status is KnowledgeObjectStatus.ACTIVE
        ):
            return KnowledgeObjectRestored(
                aggregate_id=next_object.header.id,
                payload=event_payload,
            )

        if next_object.header.status is KnowledgeObjectStatus.DELETED:
            return KnowledgeObjectDeleted(
                aggregate_id=next_object.header.id,
                payload=event_payload,
            )

        return KnowledgeObjectUpdated(
            aggregate_id=next_object.header.id,
            payload=event_payload,
        )
