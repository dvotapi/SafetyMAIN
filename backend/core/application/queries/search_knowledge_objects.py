from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects import KnowledgeObjectType, OrganizationId
from backend.core.domain.value_objects.knowledge_object_search_criteria import JSONValue


@dataclass(frozen=True, slots=True)
class SearchKnowledgeObjectsQuery:
    organization_id: OrganizationId
    object_type: KnowledgeObjectType | None = None
    status: KnowledgeObjectStatus | None = None
    metadata_equals: Mapping[str, JSONValue] = field(default_factory=dict)
    include_deleted: bool = False
    limit: int = 50
    offset: int = 0
