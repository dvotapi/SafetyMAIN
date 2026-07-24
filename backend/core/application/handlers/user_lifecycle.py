from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
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
from backend.core.domain.value_objects.refresh_session import RefreshSessionRevocationReason


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
        security_event_recorder: AuthenticationSecurityEventRecorder | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit
        self._security_event_recorder = security_event_recorder

    def handle(self, command: DeactivateUserCommand) -> User:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.USER_DEACTIVATE,
            context=audit_context,
            resource_type=AuditResourceType.USER,
            resource_id=command.user_id.value,
        )
        revoked_count = 0

        def operation() -> User:
            user = self._unit_of_work.users.get(command.user_id)
            if user.status is UserStatus.DEACTIVATED:
                raise UserAlreadyDeactivated(user.id)
            return user.model_copy(
                update={"status": UserStatus.DEACTIVATED, "updated_at": datetime.now(UTC)}
            )

        def success_spec(user: User) -> AuditRecordSpec:
            nonlocal revoked_count
            self._unit_of_work.users.save(user)
            revoked_count = self._unit_of_work.refresh_sessions.revoke_all_for_user(
                user.id,
                revoked_at=datetime.now(UTC),
                reason=RefreshSessionRevocationReason.USER_DEACTIVATED,
            )
            return AuditRecordSpec(
                action=AuditAction.USER_DEACTIVATE,
                context=audit_context,
                resource_type=AuditResourceType.USER,
                resource_id=user.id.value,
            )

        user = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        if self._security_event_recorder is not None and revoked_count > 0:
            self._security_event_recorder.record_session_revoked(
                AuthenticationAuditContext(
                    actor_user_id=audit_context.actor_user_id,
                    organization_id=audit_context.authorization_organization_id,
                ),
                user_id=user.id,
                revocation_reason=RefreshSessionRevocationReason.USER_DEACTIVATED.value,
                revoked_session_count=revoked_count,
            )
        return user
