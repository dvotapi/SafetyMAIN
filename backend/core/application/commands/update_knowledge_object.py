from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects import KnowledgeObjectId


@dataclass(frozen=True, slots=True)
class UpdateKnowledgeObjectCommand:
    object_id: KnowledgeObjectId
    status: KnowledgeObjectStatus
    payload: dict[str, Any] = field(default_factory=dict)
