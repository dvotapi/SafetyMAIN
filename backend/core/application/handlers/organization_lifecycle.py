from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.commands.organization_lifecycle import (
    ActivateOrganizationCommand,
    DeactivateOrganizationCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.exceptions import (
    CurrentOrganizationDeactivationError,
    OrganizationAlreadyActive,
    OrganizationAlreadyInactive,
)


class ActivateOrganizationHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: ActivateOrganizationCommand) -> Organization:
        organization = self._unit_of_work.organizations.get(command.organization_id)
        if organization.status is OrganizationStatus.ACTIVE:
            raise OrganizationAlreadyActive(organization.id)

        updated_organization = organization.model_copy(
            update={
                "status": OrganizationStatus.ACTIVE,
                "updated_at": datetime.now(UTC),
            }
        )
        self._unit_of_work.organizations.save(updated_organization)
        self._unit_of_work.commit()
        return updated_organization


class DeactivateOrganizationHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: DeactivateOrganizationCommand) -> Organization:
        if command.organization_id == command.authorization_organization_id:
            raise CurrentOrganizationDeactivationError(command.organization_id)

        organization = self._unit_of_work.organizations.get(command.organization_id)
        if organization.status is OrganizationStatus.DEACTIVATED:
            raise OrganizationAlreadyInactive(organization.id)

        updated_organization = organization.model_copy(
            update={
                "status": OrganizationStatus.DEACTIVATED,
                "updated_at": datetime.now(UTC),
            }
        )
        self._unit_of_work.organizations.save(updated_organization)
        self._unit_of_work.commit()
        return updated_organization
