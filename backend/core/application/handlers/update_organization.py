from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.commands.update_organization import UpdateOrganizationCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.organization import Organization, normalized_organization_name_key
from backend.core.domain.exceptions import DuplicateOrganizationName


class UpdateOrganizationHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: UpdateOrganizationCommand) -> Organization:
        organization = self._unit_of_work.organizations.get(command.organization_id)
        normalized_name = normalized_organization_name_key(command.name)
        if normalized_name != normalized_organization_name_key(organization.name):
            existing = self._unit_of_work.organizations.get_by_normalized_name(
                normalized_name
            )
            if existing is not None and existing.id != organization.id:
                raise DuplicateOrganizationName(command.name)

        updated_organization = organization.model_copy(
            update={
                "name": command.name,
                "updated_at": datetime.now(UTC),
            }
        )
        self._unit_of_work.organizations.save(updated_organization)
        self._unit_of_work.commit()
        return updated_organization
