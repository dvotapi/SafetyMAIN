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
from tests.core.audit_test_support import make_admin_audit_stack


def test_create_organization_persists_organization() -> None:
    stack = make_admin_audit_stack()
    handler = CreateOrganizationHandler(stack.uow, stack.audit)

    organization = handler.handle(
        CreateOrganizationCommand(
            name="SafetyMAIN Development Organization",
            audit_context=stack.ctx,
        )
    )

    assert organization.name == "SafetyMAIN Development Organization"
    assert organization.is_active() is True
    assert stack.uow.committed is True
    assert stack.uow.organizations.get(organization.id).name == organization.name


def test_create_organization_trims_name() -> None:
    stack = make_admin_audit_stack()
    organization = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="  Acme Safety  ", audit_context=stack.ctx)
    )

    assert organization.name == "Acme Safety"


def test_create_organization_rejects_duplicate_normalized_name() -> None:
    stack = make_admin_audit_stack()
    handler = CreateOrganizationHandler(stack.uow, stack.audit)
    handler.handle(CreateOrganizationCommand(name="Acme Safety", audit_context=stack.ctx))

    with pytest.raises(DuplicateOrganizationName):
        handler.handle(
            CreateOrganizationCommand(name="  acme safety ", audit_context=stack.ctx)
        )


def test_update_organization_renames_organization() -> None:
    stack = make_admin_audit_stack()
    organization = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Acme Safety", audit_context=stack.ctx)
    )

    updated = UpdateOrganizationHandler(stack.uow, stack.audit).handle(
        UpdateOrganizationCommand(
            organization_id=organization.id,
            name="Updated Safety",
            audit_context=stack.ctx,
        )
    )

    assert updated.name == "Updated Safety"


def test_update_organization_rejects_duplicate_name() -> None:
    stack = make_admin_audit_stack()
    CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Acme Safety", audit_context=stack.ctx)
    )
    other = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Beta Safety", audit_context=stack.ctx)
    )

    with pytest.raises(DuplicateOrganizationName):
        UpdateOrganizationHandler(stack.uow, stack.audit).handle(
            UpdateOrganizationCommand(
                organization_id=other.id,
                name="Acme Safety",
                audit_context=stack.ctx,
            )
        )


def test_activate_and_deactivate_organization() -> None:
    stack = make_admin_audit_stack()
    organization = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Acme Safety", is_active=False, audit_context=stack.ctx)
    )
    assert organization.status is OrganizationStatus.DEACTIVATED

    activated = ActivateOrganizationHandler(stack.uow, stack.audit).handle(
        ActivateOrganizationCommand(organization_id=organization.id, audit_context=stack.ctx)
    )
    assert activated.status is OrganizationStatus.ACTIVE

    other_id = OrganizationId(value=uuid4())
    now = datetime.now(UTC)
    stack.uow.organizations.add(
        Organization(
            id=other_id,
            name="Authorization Org",
            status=OrganizationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    )
    deactivated = DeactivateOrganizationHandler(stack.uow, stack.audit).handle(
        DeactivateOrganizationCommand(
            organization_id=activated.id,
            authorization_organization_id=other_id,
            audit_context=stack.ctx,
        )
    )
    assert deactivated.status is OrganizationStatus.DEACTIVATED


def test_activate_already_active_organization_raises() -> None:
    stack = make_admin_audit_stack()
    organization = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Acme Safety", audit_context=stack.ctx)
    )

    with pytest.raises(OrganizationAlreadyActive):
        ActivateOrganizationHandler(stack.uow, stack.audit).handle(
            ActivateOrganizationCommand(
                organization_id=organization.id,
                audit_context=stack.ctx,
            )
        )


def test_deactivate_already_inactive_organization_raises() -> None:
    stack = make_admin_audit_stack()
    organization = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Acme Safety", is_active=False, audit_context=stack.ctx)
    )
    auth_org_id = OrganizationId(value=uuid4())

    with pytest.raises(OrganizationAlreadyInactive):
        DeactivateOrganizationHandler(stack.uow, stack.audit).handle(
            DeactivateOrganizationCommand(
                organization_id=organization.id,
                authorization_organization_id=auth_org_id,
                audit_context=stack.ctx,
            )
        )


def test_deactivate_current_authorization_organization_raises() -> None:
    stack = make_admin_audit_stack()
    organization = CreateOrganizationHandler(stack.uow, stack.audit).handle(
        CreateOrganizationCommand(name="Acme Safety", audit_context=stack.ctx)
    )

    with pytest.raises(CurrentOrganizationDeactivationError):
        DeactivateOrganizationHandler(stack.uow, stack.audit).handle(
            DeactivateOrganizationCommand(
                organization_id=organization.id,
                authorization_organization_id=organization.id,
                audit_context=stack.ctx,
            )
        )


def test_list_organizations_supports_filtering_and_sorting() -> None:
    stack = make_admin_audit_stack()
    create_handler = CreateOrganizationHandler(stack.uow, stack.audit)
    create_handler.handle(CreateOrganizationCommand(name="Alpha Org", audit_context=stack.ctx))
    create_handler.handle(
        CreateOrganizationCommand(name="Beta Org", is_active=False, audit_context=stack.ctx)
    )

    result = ListOrganizationsHandler(stack.uow).handle(
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
