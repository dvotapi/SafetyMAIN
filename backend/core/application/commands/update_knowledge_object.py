from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectVersion,
    OrganizationId,
)


@dataclass(frozen=True, slots=True)
class UpdateKnowledgeObjectCommand:
    object_id: KnowledgeObjectId
    organization_id: OrganizationId
    expected_version: KnowledgeObjectVersion
    status: KnowledgeObjectStatus | None = None
    payload: dict[str, Any] = field(default_factory=dict)
