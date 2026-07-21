from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.audit.metadata import changed_fields_metadata
from backend.core.application.commands.update_user import UpdateUserCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import DuplicateUserEmail
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class UpdateUserHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: UpdateUserCommand) -> User:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.USER_UPDATE,
            context=audit_context,
            resource_type=AuditResourceType.USER,
            resource_id=command.user_id.value,
        )

        def operation() -> tuple[User, dict[str, object]]:
            user = self._unit_of_work.users.get(command.user_id)
            next_email = user.email if command.email is None else command.email.strip().lower()
            next_display_name = (
                user.display_name if command.display_name is None else command.display_name
            )
            next_status = user.status
            if command.is_active is not None:
                next_status = (
                    UserStatus.ACTIVE if command.is_active else UserStatus.DEACTIVATED
                )

            if next_email != user.email:
                existing = self._unit_of_work.users.get_by_email(next_email)
                if existing is not None and existing.id != user.id:
                    raise DuplicateUserEmail(next_email)

            changed_fields: list[str] = []
            if next_display_name != user.display_name:
                changed_fields.append("display_name")
            if next_email != user.email:
                changed_fields.append("email")
            if next_status != user.status:
                changed_fields.append("status")

            updated_user = user.model_copy(
                update={
                    "email": next_email,
                    "display_name": next_display_name,
                    "status": next_status,
                    "updated_at": datetime.now(UTC),
                }
            )
            return updated_user, changed_fields_metadata(*changed_fields)

        def success_spec(result: tuple[User, dict[str, object]]) -> AuditRecordSpec:
            updated_user, metadata = result
            self._unit_of_work.users.save(updated_user)
            return AuditRecordSpec(
                action=AuditAction.USER_UPDATE,
                context=audit_context,
                resource_type=AuditResourceType.USER,
                resource_id=updated_user.id.value,
                metadata=metadata,
            )

        updated_user, _ = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return updated_user
