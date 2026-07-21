from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.commands.create_organization import CreateOrganizationCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.organization import (
    Organization,
    OrganizationStatus,
    normalized_organization_name_key,
)
from backend.core.domain.exceptions import DuplicateOrganizationName
from backend.core.domain.value_objects import OrganizationId


class CreateOrganizationHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: CreateOrganizationCommand) -> Organization:
        organization = Organization(
            id=OrganizationId(value=uuid4()),
            name=command.name,
            status=(
                OrganizationStatus.ACTIVE
                if command.is_active
                else OrganizationStatus.DEACTIVATED
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        normalized_name = normalized_organization_name_key(organization.name)
        if (
            self._unit_of_work.organizations.get_by_normalized_name(normalized_name)
            is not None
        ):
            raise DuplicateOrganizationName(organization.name)

        self._unit_of_work.organizations.add(organization)
        self._unit_of_work.commit()
        return organization
