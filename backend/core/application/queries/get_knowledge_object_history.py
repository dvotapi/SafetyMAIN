from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import KnowledgeObjectId, OrganizationId


@dataclass(frozen=True, slots=True)
class GetKnowledgeObjectHistoryQuery:
    organization_id: OrganizationId
    object_id: KnowledgeObjectId
