from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.domain.entities.knowledge_object import KnowledgeObject, KnowledgeObjectStatus
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
)


def organization_headers(organization_id: UUID) -> dict[str, str]:
    return {ORGANIZATION_ID_HEADER: str(organization_id)}


def create_object(
    client: TestClient,
    organization_id: UUID,
    *,
    object_type: str = "policy",
    metadata: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/knowledge-objects",
        headers=headers or organization_headers(organization_id),
        json={
            "type": object_type,
            "metadata": metadata or {"title": "Information Security Policy"},
        },
    )
    assert response.status_code == 201
    return response.json()


def seed_knowledge_object(
    knowledge_objects: InMemoryKnowledgeObjectRepository,
    organization_id: UUID,
    *,
    object_type: str = "policy",
    status: KnowledgeObjectStatus = KnowledgeObjectStatus.ACTIVE,
    metadata: dict[str, object] | None = None,
) -> KnowledgeObject:
    unit_of_work = InMemoryUnitOfWork(
        knowledge_objects=knowledge_objects,
        relations=InMemoryKnowledgeObjectRelationRepository(),
    )
    return CreateKnowledgeObjectHandler(unit_of_work).handle(
        CreateKnowledgeObjectCommand(
            object_type=object_type,
            organization_id=organization_id,
            status=status,
            payload=metadata or {"title": "Seeded object"},
        )
    )
