from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus


@dataclass(frozen=True, slots=True)
class CreateKnowledgeObjectCommand:
    object_type: str
    organization_id: UUID
    status: KnowledgeObjectStatus = KnowledgeObjectStatus.DRAFT
    payload: dict[str, Any] = field(default_factory=dict)
