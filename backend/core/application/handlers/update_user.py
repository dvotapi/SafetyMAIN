from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.commands.update_user import UpdateUserCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import DuplicateUserEmail


class UpdateUserHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: UpdateUserCommand) -> User:
        user = self._unit_of_work.users.get(command.user_id)
        next_email = user.email if command.email is None else command.email.strip().lower()
        next_display_name = (
            user.display_name if command.display_name is None else command.display_name
        )
        next_status = user.status
        if command.is_active is not None:
            next_status = UserStatus.ACTIVE if command.is_active else UserStatus.DEACTIVATED

        if next_email != user.email:
            existing = self._unit_of_work.users.get_by_email(next_email)
            if existing is not None and existing.id != user.id:
                raise DuplicateUserEmail(next_email)

        updated_user = user.model_copy(
            update={
                "email": next_email,
                "display_name": next_display_name,
                "status": next_status,
                "updated_at": datetime.now(UTC),
            }
        )
        self._unit_of_work.users.save(updated_user)
        self._unit_of_work.commit()
        return updated_user
