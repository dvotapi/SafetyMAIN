from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import OrganizationId


@dataclass(frozen=True, slots=True)
class UpdateOrganizationCommand:
    organization_id: OrganizationId
    name: str
