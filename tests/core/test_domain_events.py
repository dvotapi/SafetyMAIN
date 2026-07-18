from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.entities.knowledge_object_relation import (
    KnowledgeObjectRelation,
)
from backend.core.domain.events import (
    KnowledgeObjectArchived,
    KnowledgeObjectCreated,
    KnowledgeObjectDeleted,
    KnowledgeObjectRelationCreated,
    KnowledgeObjectRelationRemoved,
    KnowledgeObjectRestored,
    KnowledgeObjectUpdated,
)
from backend.core.domain.services import (
    KnowledgeObjectRelationService,
    KnowledgeObjectService,
)
from backend.core.domain.value_objects import KnowledgeObjectRelationType


def _create_knowledge_object(
    status: KnowledgeObjectStatus,
    organization_id: UUID | None = None,
) -> KnowledgeObject:
    now = datetime.now(UTC)
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=uuid4(),
            object_type="Organization",
            organization_id=organization_id or uuid4(),
            status=status,
            version=1,
            created_at=now,
            updated_at=now,
        ),
        payload={"name": "SafetyMAIN"},
    )


def test_domain_event_creation() -> None:
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.DRAFT)

    event = KnowledgeObjectCreated(
        aggregate_id=knowledge_object.header.id,
        payload={"version": knowledge_object.header.version.value},
    )

    assert event.event_type == "knowledge_object.created"
    assert event.aggregate_id == knowledge_object.header.id
    assert event.payload == {"version": 1}


def test_domain_event_is_immutable() -> None:
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.DRAFT)
    event = KnowledgeObjectCreated(aggregate_id=knowledge_object.header.id)

    with pytest.raises(ValidationError):
        event.event_type = "changed"


def test_domain_event_serialization() -> None:
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.DRAFT)
    event = KnowledgeObjectCreated(
        aggregate_id=knowledge_object.header.id,
        payload={"version": knowledge_object.header.version.value},
    )

    serialized_event = event.model_dump(mode="json")

    assert serialized_event["event_type"] == "knowledge_object.created"
    assert serialized_event["aggregate_id"]["value"] == str(
        knowledge_object.header.id.value
    )
    assert serialized_event["payload"] == {"version": 1}


def test_knowledge_object_service_returns_updated_event() -> None:
    service = KnowledgeObjectService()
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.DRAFT)

    _updated_object, event = service.create_next_version(
        knowledge_object,
        status=KnowledgeObjectStatus.ACTIVE,
        payload={"name": "SafetyMAIN Updated"},
    )

    assert isinstance(event, KnowledgeObjectUpdated)
    assert event.payload["previous_version"] == 1
    assert event.payload["current_version"] == 2


def test_knowledge_object_service_returns_archived_event() -> None:
    service = KnowledgeObjectService()
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.ACTIVE)

    _archived_object, event = service.create_next_version(
        knowledge_object,
        status=KnowledgeObjectStatus.ARCHIVED,
    )

    assert isinstance(event, KnowledgeObjectArchived)
    assert event.event_type == "knowledge_object.archived"


def test_knowledge_object_service_returns_restored_event() -> None:
    service = KnowledgeObjectService()
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.ARCHIVED)

    _restored_object, event = service.create_next_version(
        knowledge_object,
        status=KnowledgeObjectStatus.ACTIVE,
    )

    assert isinstance(event, KnowledgeObjectRestored)
    assert event.event_type == "knowledge_object.restored"


def test_knowledge_object_service_returns_deleted_event() -> None:
    service = KnowledgeObjectService()
    knowledge_object = _create_knowledge_object(KnowledgeObjectStatus.ACTIVE)

    _deleted_object, event = service.delete(knowledge_object)

    assert isinstance(event, KnowledgeObjectDeleted)
    assert event.event_type == "knowledge_object.deleted"


def test_relation_service_returns_created_event() -> None:
    service = KnowledgeObjectRelationService()
    source_object = _create_knowledge_object(KnowledgeObjectStatus.ACTIVE)
    target_object = _create_knowledge_object(
        KnowledgeObjectStatus.ACTIVE,
        organization_id=source_object.header.organization_id.value,
    )

    _relation, event = service.create_relation(
        source_object=source_object,
        target_object=target_object,
        relation_type=KnowledgeObjectRelationType(value="addresses"),
    )

    assert isinstance(event, KnowledgeObjectRelationCreated)
    assert event.event_type == "knowledge_object_relation.created"


def test_relation_service_returns_removed_event() -> None:
    service = KnowledgeObjectRelationService()
    source_object = _create_knowledge_object(KnowledgeObjectStatus.ACTIVE)
    target_object = _create_knowledge_object(KnowledgeObjectStatus.ACTIVE)
    relation = KnowledgeObjectRelation(
        relation_id=uuid4(),
        organization_id=source_object.header.organization_id,
        source_object_id=source_object.header.id,
        target_object_id=target_object.header.id,
        relation_type=KnowledgeObjectRelationType(value="addresses"),
        created_at=datetime.now(UTC),
    )

    event = service.remove_relation(relation)

    assert isinstance(event, KnowledgeObjectRelationRemoved)
    assert event.event_type == "knowledge_object_relation.removed"
