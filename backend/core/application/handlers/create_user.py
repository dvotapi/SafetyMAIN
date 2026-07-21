from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.commands.create_user import CreateUserCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import DuplicateUserEmail
from backend.core.domain.value_objects import UserId


class CreateUserHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: CreateUserCommand) -> User:
        normalized_email = command.email.strip().lower()
        if self._unit_of_work.users.get_by_email(normalized_email) is not None:
            raise DuplicateUserEmail(normalized_email)

        now = datetime.now(UTC)
        user = User(
            id=UserId(value=uuid4()),
            display_name=command.display_name,
            email=normalized_email,
            status=UserStatus.ACTIVE if command.is_active else UserStatus.DEACTIVATED,
            created_at=now,
            updated_at=now,
        )

        self._unit_of_work.users.add(user)
        self._unit_of_work.commit()

        return user
