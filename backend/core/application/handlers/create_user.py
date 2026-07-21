from __future__ import annotations

from uuid import uuid4

from datetime import UTC, datetime

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import run_audited_admin_operation
from backend.core.application.commands.create_user import CreateUserCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import DuplicateUserEmail
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class CreateUserHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: CreateUserCommand) -> User:
        audit_context = command.audit_context
        if audit_context is None:
            raise ValueError("Audit context is required for administrative user creation.")

        failure_spec = AuditRecordSpec(
            action=AuditAction.USER_CREATE,
            context=audit_context,
            resource_type=AuditResourceType.USER,
        )

        def operation() -> User:
            normalized_email = command.email.strip().lower()
            if self._unit_of_work.users.get_by_email(normalized_email) is not None:
                raise DuplicateUserEmail(normalized_email)

            now = datetime.now(UTC)
            return User(
                id=UserId(value=uuid4()),
                display_name=command.display_name,
                email=normalized_email,
                status=UserStatus.ACTIVE if command.is_active else UserStatus.DEACTIVATED,
                created_at=now,
                updated_at=now,
            )

        def success_spec(user: User) -> AuditRecordSpec:
            self._unit_of_work.users.add(user)
            return AuditRecordSpec(
                action=AuditAction.USER_CREATE,
                context=audit_context,
                resource_type=AuditResourceType.USER,
                resource_id=user.id.value,
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
