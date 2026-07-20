from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.core.domain.value_objects import OrganizationId


@dataclass(frozen=True, slots=True)
class RemoveKnowledgeObjectRelationCommand:
    organization_id: OrganizationId
    relation_id: UUID
