from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import OrganizationId


class OrganizationError(SafetyMainDomainError):
    """Base class for Organization domain errors."""


class OrganizationNotFound(OrganizationError):
    def __init__(self, organization_id: OrganizationId) -> None:
        self.organization_id = organization_id
        super().__init__(f"Organization was not found: {organization_id.value}")


class DuplicateOrganizationName(OrganizationError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__("Organization name already exists.")


class OrganizationAlreadyActive(OrganizationError):
    def __init__(self, organization_id: OrganizationId) -> None:
        self.organization_id = organization_id
        super().__init__("Organization is already active.")


class OrganizationAlreadyInactive(OrganizationError):
    def __init__(self, organization_id: OrganizationId) -> None:
        self.organization_id = organization_id
        super().__init__("Organization is already inactive.")


class CurrentOrganizationDeactivationError(OrganizationError):
    def __init__(self, organization_id: OrganizationId) -> None:
        self.organization_id = organization_id
        super().__init__(
            "The current authorization organization cannot be deactivated."
        )
