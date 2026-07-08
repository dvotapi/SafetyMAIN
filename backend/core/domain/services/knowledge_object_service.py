from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.value_objects import KnowledgeObjectVersion


class KnowledgeObjectService:
    def create_next_version(
        self,
        knowledge_object: KnowledgeObject,
        *,
        status: KnowledgeObjectStatus,
        payload: dict[str, Any] | None = None,
    ) -> KnowledgeObject:
        return KnowledgeObject(
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
