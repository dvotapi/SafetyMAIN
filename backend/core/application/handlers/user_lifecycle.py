from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.commands.user_lifecycle import (
    ActivateUserCommand,
    DeactivateUserCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import UserAlreadyActive, UserAlreadyDeactivated


class ActivateUserHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: ActivateUserCommand) -> User:
        user = self._unit_of_work.users.get(command.user_id)
        if user.status is UserStatus.ACTIVE:
            raise UserAlreadyActive(user.id)

        updated_user = user.model_copy(
            update={
                "status": UserStatus.ACTIVE,
                "updated_at": datetime.now(UTC),
            }
        )
        self._unit_of_work.users.save(updated_user)
        self._unit_of_work.commit()
        return updated_user


class DeactivateUserHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: DeactivateUserCommand) -> User:
        user = self._unit_of_work.users.get(command.user_id)
        if user.status is UserStatus.DEACTIVATED:
            raise UserAlreadyDeactivated(user.id)

        updated_user = user.model_copy(
            update={
                "status": UserStatus.DEACTIVATED,
                "updated_at": datetime.now(UTC),
            }
        )
        self._unit_of_work.users.save(updated_user)
        self._unit_of_work.commit()
        return updated_user
