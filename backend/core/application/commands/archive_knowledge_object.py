from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import KnowledgeObjectId


@dataclass(frozen=True, slots=True)
class ArchiveKnowledgeObjectCommand:
    object_id: KnowledgeObjectId
