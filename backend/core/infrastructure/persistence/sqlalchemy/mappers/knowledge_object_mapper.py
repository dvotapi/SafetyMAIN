from __future__ import annotations

from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
)
from backend.core.infrastructure.persistence.sqlalchemy.models import (
    KnowledgeObjectModel,
    KnowledgeObjectVersionModel,
)


def to_model(knowledge_object: KnowledgeObject) -> KnowledgeObjectModel:
    return KnowledgeObjectModel(
        id=knowledge_object.header.id.value,
        organization_id=knowledge_object.header.organization_id.value,
        object_type=knowledge_object.header.object_type.value,
        status=knowledge_object.header.status.value,
        version=knowledge_object.header.version.value,
        metadata_=_to_plain_json(knowledge_object.payload),
        created_at=knowledge_object.header.created_at,
        updated_at=knowledge_object.header.updated_at,
    )


def apply_to_model(
    model: KnowledgeObjectModel,
    knowledge_object: KnowledgeObject,
) -> None:
    model.organization_id = knowledge_object.header.organization_id.value
    model.object_type = knowledge_object.header.object_type.value
    model.status = knowledge_object.header.status.value
    model.version = knowledge_object.header.version.value
    model.metadata_ = _to_plain_json(knowledge_object.payload)
    model.created_at = knowledge_object.header.created_at
    model.updated_at = knowledge_object.header.updated_at


def to_history_model(
    knowledge_object: KnowledgeObject,
    recorded_at: datetime | None = None,
) -> KnowledgeObjectVersionModel:
    return KnowledgeObjectVersionModel(
        history_id=uuid4(),
        knowledge_object_id=knowledge_object.header.id.value,
        organization_id=knowledge_object.header.organization_id.value,
        object_type=knowledge_object.header.object_type.value,
        status=knowledge_object.header.status.value,
        version=knowledge_object.header.version.value,
        metadata_=_to_plain_json(knowledge_object.payload),
        created_at=knowledge_object.header.created_at,
        updated_at=knowledge_object.header.updated_at,
        recorded_at=recorded_at or datetime.now(UTC),
    )


def to_domain(model: KnowledgeObjectModel) -> KnowledgeObject:
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=model.id,
            object_type=model.object_type,
            organization_id=model.organization_id,
            status=model.status,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        ),
        payload=dict(model.metadata_),
    )


def to_domain_from_history(model: KnowledgeObjectVersionModel) -> KnowledgeObject:
    return KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=model.knowledge_object_id,
            object_type=model.object_type,
            organization_id=model.organization_id,
            status=model.status,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        ),
        payload=dict(model.metadata_),
    )


def _to_plain_json(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: _to_plain_json(item) for key, item in value.items()}

    if isinstance(value, dict):
        return {key: _to_plain_json(item) for key, item in value.items()}

    if isinstance(value, list | tuple):
        return [_to_plain_json(item) for item in value]

    return value
