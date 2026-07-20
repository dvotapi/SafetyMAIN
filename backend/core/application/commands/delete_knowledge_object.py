from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import KnowledgeObjectId, OrganizationId


@dataclass(frozen=True, slots=True)
class DeleteKnowledgeObjectCommand:
    object_id: KnowledgeObjectId
    organization_id: OrganizationId
