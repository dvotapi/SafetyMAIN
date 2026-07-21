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
from backend.core.application.commands.user_lifecycle import (
    ActivateUserCommand,
    DeactivateUserCommand,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import UserAlreadyActive, UserAlreadyDeactivated
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class ActivateUserHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: ActivateUserCommand) -> User:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.USER_ACTIVATE,
            context=audit_context,
            resource_type=AuditResourceType.USER,
            resource_id=command.user_id.value,
        )

        def operation() -> User:
            user = self._unit_of_work.users.get(command.user_id)
            if user.status is UserStatus.ACTIVE:
                raise UserAlreadyActive(user.id)
            return user.model_copy(
                update={"status": UserStatus.ACTIVE, "updated_at": datetime.now(UTC)}
            )

        def success_spec(user: User) -> AuditRecordSpec:
            self._unit_of_work.users.save(user)
            return AuditRecordSpec(
                action=AuditAction.USER_ACTIVATE,
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


class DeactivateUserHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: DeactivateUserCommand) -> User:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.USER_DEACTIVATE,
            context=audit_context,
            resource_type=AuditResourceType.USER,
            resource_id=command.user_id.value,
        )

        def operation() -> User:
            user = self._unit_of_work.users.get(command.user_id)
            if user.status is UserStatus.DEACTIVATED:
                raise UserAlreadyDeactivated(user.id)
            return user.model_copy(
                update={"status": UserStatus.DEACTIVATED, "updated_at": datetime.now(UTC)}
            )

        def success_spec(user: User) -> AuditRecordSpec:
            self._unit_of_work.users.save(user)
            return AuditRecordSpec(
                action=AuditAction.USER_DEACTIVATE,
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
