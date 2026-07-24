from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import (
    AffectedSubject,
    HazardCategory,
    HazardSource,
    HazardStatus,
    SafetyDirection,
)


@dataclass(frozen=True, slots=True)
class HazardQuery:
    organization_id: OrganizationId
    status: HazardStatus | None = None
    category: HazardCategory | None = None
    safety_direction: SafetyDirection | None = None
    source: HazardSource | None = None
    affected_subject: AffectedSubject | None = None
    identified_from: datetime | None = None
    identified_to: datetime | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    search: str | None = None
    include_archived: bool = False
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class HazardPage:
    items: tuple[Hazard, ...]
    total: int
    offset: int
    limit: int
