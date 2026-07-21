from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import OrganizationId


@dataclass(frozen=True, slots=True)
class ActivateOrganizationCommand:
    organization_id: OrganizationId


@dataclass(frozen=True, slots=True)
class DeactivateOrganizationCommand:
    organization_id: OrganizationId
    authorization_organization_id: OrganizationId
