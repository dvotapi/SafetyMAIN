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
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_create_user_persists_user() -> None:
    uow = InMemoryUnitOfWork()
    handler = CreateUserHandler(uow)

    user = handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
        )
    )

    assert user.email == "operator@example.com"
    assert user.is_active() is True
    assert uow.committed is True
    assert uow.users.get(user.id).display_name == "Safety Operator"


def test_create_user_rejects_duplicate_email() -> None:
    uow = InMemoryUnitOfWork()
    handler = CreateUserHandler(uow)
    handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
        )
    )

    with pytest.raises(DuplicateUserEmail):
        handler.handle(
            CreateUserCommand(
                email="operator@example.com",
                display_name="Another Operator",
            )
        )

    assert uow.committed is True


def test_update_user_changes_profile_fields() -> None:
    uow = InMemoryUnitOfWork()
    create_handler = CreateUserHandler(uow)
    user = create_handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
        )
    )

    updated = UpdateUserHandler(uow).handle(
        UpdateUserCommand(
            user_id=user.id,
            display_name="Updated Operator",
            email="updated@example.com",
        )
    )

    assert updated.display_name == "Updated Operator"
    assert updated.email == "updated@example.com"


def test_activate_and_deactivate_user() -> None:
    uow = InMemoryUnitOfWork()
    create_handler = CreateUserHandler(uow)
    user = create_handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            is_active=False,
        )
    )
    assert user.status is UserStatus.DEACTIVATED

    activated = ActivateUserHandler(uow).handle(ActivateUserCommand(user_id=user.id))
    assert activated.status is UserStatus.ACTIVE

    deactivated = DeactivateUserHandler(uow).handle(
        DeactivateUserCommand(user_id=user.id)
    )
    assert deactivated.status is UserStatus.DEACTIVATED


def test_activate_already_active_user_raises() -> None:
    uow = InMemoryUnitOfWork()
    user = CreateUserHandler(uow).handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
        )
    )

    with pytest.raises(UserAlreadyActive):
        ActivateUserHandler(uow).handle(ActivateUserCommand(user_id=user.id))


def test_deactivate_already_deactivated_user_raises() -> None:
    uow = InMemoryUnitOfWork()
    user = CreateUserHandler(uow).handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            is_active=False,
        )
    )

    with pytest.raises(UserAlreadyDeactivated):
        DeactivateUserHandler(uow).handle(DeactivateUserCommand(user_id=user.id))
