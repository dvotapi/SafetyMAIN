from __future__ import annotations

import pytest

from backend.core.application.commands.create_user import CreateUserCommand
from backend.core.application.commands.update_user import UpdateUserCommand
from backend.core.application.commands.user_lifecycle import (
    ActivateUserCommand,
    DeactivateUserCommand,
)
from backend.core.application.handlers.create_user import CreateUserHandler
from backend.core.application.handlers.update_user import UpdateUserHandler
from backend.core.application.handlers.user_lifecycle import (
    ActivateUserHandler,
    DeactivateUserHandler,
)
from backend.core.domain.entities.user import UserStatus
from backend.core.domain.exceptions import (
    DuplicateUserEmail,
    UserAlreadyActive,
    UserAlreadyDeactivated,
)
from tests.core.audit_test_support import make_admin_audit_stack


def test_create_user_persists_user() -> None:
    stack = make_admin_audit_stack()
    handler = CreateUserHandler(stack.uow, stack.audit)

    user = handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            audit_context=stack.ctx,
        )
    )

    assert user.email == "operator@example.com"
    assert user.is_active() is True
    assert stack.uow.committed is True
    assert stack.uow.users.get(user.id).display_name == "Safety Operator"


def test_create_user_rejects_duplicate_email() -> None:
    stack = make_admin_audit_stack()
    handler = CreateUserHandler(stack.uow, stack.audit)
    handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            audit_context=stack.ctx,
        )
    )

    with pytest.raises(DuplicateUserEmail):
        handler.handle(
            CreateUserCommand(
                email="operator@example.com",
                display_name="Another Operator",
                audit_context=stack.ctx,
            )
        )

    assert stack.uow.users.get_by_email("operator@example.com") is not None


def test_update_user_changes_profile_fields() -> None:
    stack = make_admin_audit_stack()
    create_handler = CreateUserHandler(stack.uow, stack.audit)
    user = create_handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            audit_context=stack.ctx,
        )
    )

    updated = UpdateUserHandler(stack.uow, stack.audit).handle(
        UpdateUserCommand(
            user_id=user.id,
            display_name="Updated Operator",
            email="updated@example.com",
            audit_context=stack.ctx,
        )
    )

    assert updated.display_name == "Updated Operator"
    assert updated.email == "updated@example.com"


def test_activate_and_deactivate_user() -> None:
    stack = make_admin_audit_stack()
    create_handler = CreateUserHandler(stack.uow, stack.audit)
    user = create_handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            is_active=False,
            audit_context=stack.ctx,
        )
    )
    assert user.status is UserStatus.DEACTIVATED

    activated = ActivateUserHandler(stack.uow, stack.audit).handle(
        ActivateUserCommand(user_id=user.id, audit_context=stack.ctx)
    )
    assert activated.status is UserStatus.ACTIVE

    deactivated = DeactivateUserHandler(stack.uow, stack.audit).handle(
        DeactivateUserCommand(user_id=user.id, audit_context=stack.ctx)
    )
    assert deactivated.status is UserStatus.DEACTIVATED


def test_activate_already_active_user_raises() -> None:
    stack = make_admin_audit_stack()
    user = CreateUserHandler(stack.uow, stack.audit).handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            audit_context=stack.ctx,
        )
    )

    with pytest.raises(UserAlreadyActive):
        ActivateUserHandler(stack.uow, stack.audit).handle(
            ActivateUserCommand(user_id=user.id, audit_context=stack.ctx)
        )


def test_deactivate_already_deactivated_user_raises() -> None:
    stack = make_admin_audit_stack()
    user = CreateUserHandler(stack.uow, stack.audit).handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            is_active=False,
            audit_context=stack.ctx,
        )
    )

    with pytest.raises(UserAlreadyDeactivated):
        DeactivateUserHandler(stack.uow, stack.audit).handle(
            DeactivateUserCommand(user_id=user.id, audit_context=stack.ctx)
        )
