from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.commands.create_organization import CreateOrganizationCommand
from backend.core.application.commands.organization_lifecycle import (
    ActivateOrganizationCommand,
    DeactivateOrganizationCommand,
)
from backend.core.application.commands.update_organization import UpdateOrganizationCommand
from backend.core.application.handlers.create_organization import CreateOrganizationHandler
from backend.core.application.handlers.list_organizations import ListOrganizationsHandler
from backend.core.application.handlers.organization_lifecycle import (
    ActivateOrganizationHandler,
    DeactivateOrganizationHandler,
)
from backend.core.application.handlers.update_organization import UpdateOrganizationHandler
from backend.core.application.queries.list_organizations import ListOrganizationsQuery
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.exceptions import (
    CurrentOrganizationDeactivationError,
    DuplicateOrganizationName,
    OrganizationAlreadyActive,
    OrganizationAlreadyInactive,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_create_organization_persists_organization() -> None:
    uow = InMemoryUnitOfWork()
    handler = CreateOrganizationHandler(uow)

    organization = handler.handle(
        CreateOrganizationCommand(name="SafetyMAIN Development Organization")
    )

    assert organization.name == "SafetyMAIN Development Organization"
    assert organization.is_active() is True
    assert uow.committed is True
    assert uow.organizations.get(organization.id).name == organization.name


def test_create_organization_trims_name() -> None:
    uow = InMemoryUnitOfWork()
    organization = CreateOrganizationHandler(uow).handle(
        CreateOrganizationCommand(name="  Acme Safety  ")
    )

    assert organization.name == "Acme Safety"


def test_create_organization_rejects_duplicate_normalized_name() -> None:
    uow = InMemoryUnitOfWork()
    handler = CreateOrganizationHandler(uow)
    handler.handle(CreateOrganizationCommand(name="Acme Safety"))

    with pytest.raises(DuplicateOrganizationName):
        handler.handle(CreateOrganizationCommand(name=" acme safety "))

    assert uow.committed is True


def test_update_organization_renames_organization() -> None:
    uow = InMemoryUnitOfWork()
    organization = CreateOrganizationHandler(uow).handle(
        CreateOrganizationCommand(name="Acme Safety")
    )

    updated = UpdateOrganizationHandler(uow).handle(
        UpdateOrganizationCommand(
            organization_id=organization.id,
            name="Acme Safety International",
        )
    )

    assert updated.name == "Acme Safety International"


def test_update_organization_rejects_duplicate_name() -> None:
    uow = InMemoryUnitOfWork()
    create_handler = CreateOrganizationHandler(uow)
    first = create_handler.handle(CreateOrganizationCommand(name="Alpha Org"))
    create_handler.handle(CreateOrganizationCommand(name="Beta Org"))

    with pytest.raises(DuplicateOrganizationName):
        UpdateOrganizationHandler(uow).handle(
            UpdateOrganizationCommand(
                organization_id=first.id,
                name="beta org",
            )
        )


def test_activate_and_deactivate_organization() -> None:
    uow = InMemoryUnitOfWork()
    organization = CreateOrganizationHandler(uow).handle(
        CreateOrganizationCommand(name="Acme Safety", is_active=False)
    )
    assert organization.status is OrganizationStatus.DEACTIVATED

    activated = ActivateOrganizationHandler(uow).handle(
        ActivateOrganizationCommand(organization_id=organization.id)
    )
    assert activated.status is OrganizationStatus.ACTIVE

    other_id = OrganizationId(value=uuid4())
    now = datetime.now(UTC)
    uow.organizations.add(
        Organization(
            id=other_id,
            name="Authorization Org",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    deactivated = DeactivateOrganizationHandler(uow).handle(
        DeactivateOrganizationCommand(
            organization_id=activated.id,
            authorization_organization_id=other_id,
        )
    )
    assert deactivated.status is OrganizationStatus.DEACTIVATED


def test_activate_already_active_organization_raises() -> None:
    uow = InMemoryUnitOfWork()
    organization = CreateOrganizationHandler(uow).handle(
        CreateOrganizationCommand(name="Acme Safety")
    )

    with pytest.raises(OrganizationAlreadyActive):
        ActivateOrganizationHandler(uow).handle(
            ActivateOrganizationCommand(organization_id=organization.id)
        )


def test_deactivate_already_inactive_organization_raises() -> None:
    uow = InMemoryUnitOfWork()
    organization = CreateOrganizationHandler(uow).handle(
        CreateOrganizationCommand(name="Acme Safety", is_active=False)
    )
    auth_org_id = OrganizationId(value=uuid4())

    with pytest.raises(OrganizationAlreadyInactive):
        DeactivateOrganizationHandler(uow).handle(
            DeactivateOrganizationCommand(
                organization_id=organization.id,
                authorization_organization_id=auth_org_id,
            )
        )


def test_deactivate_current_authorization_organization_raises() -> None:
    uow = InMemoryUnitOfWork()
    organization = CreateOrganizationHandler(uow).handle(
        CreateOrganizationCommand(name="Acme Safety")
    )

    with pytest.raises(CurrentOrganizationDeactivationError):
        DeactivateOrganizationHandler(uow).handle(
            DeactivateOrganizationCommand(
                organization_id=organization.id,
                authorization_organization_id=organization.id,
            )
        )


def test_list_organizations_supports_filtering_and_sorting() -> None:
    uow = InMemoryUnitOfWork()
    create_handler = CreateOrganizationHandler(uow)
    create_handler.handle(CreateOrganizationCommand(name="Alpha Org"))
    create_handler.handle(
        CreateOrganizationCommand(name="Beta Org", is_active=False)
    )

    result = ListOrganizationsHandler(uow).handle(
        ListOrganizationsQuery(
            offset=0,
            limit=10,
            is_active=True,
            name="alpha",
            sort_ascending=False,
        )
    )

    assert result.total == 1
    assert result.items[0].name == "Alpha Org"
