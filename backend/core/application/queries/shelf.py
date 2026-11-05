"""Queries of the document shelf (TASK-P11-012 §2.5)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import ShelfSlotId

SEARCH_DEFAULT_LIMIT = 50
SEARCH_MAX_LIMIT = 100
SEARCH_QUERY_MAX_LENGTH = 100


@dataclass(frozen=True, slots=True)
class ShelfCapabilities:
    """What the current user may do; drives ``available_actions`` (§2.2)."""

    can_curate: bool = False
    can_create_document: bool = False
    can_update_document: bool = False


@dataclass(frozen=True, slots=True)
class GetShelfOverviewQuery:
    organization_id: OrganizationId


@dataclass(frozen=True, slots=True)
class GetShelfSectionSlotsQuery:
    organization_id: OrganizationId
    section_code: str


@dataclass(frozen=True, slots=True)
class SearchShelfSlotsQuery:
    organization_id: OrganizationId
    query: str
    limit: int = SEARCH_DEFAULT_LIMIT


@dataclass(frozen=True, slots=True)
class GetShelfSlotQuery:
    organization_id: OrganizationId
    slot_id: ShelfSlotId
    capabilities: ShelfCapabilities = ShelfCapabilities()
