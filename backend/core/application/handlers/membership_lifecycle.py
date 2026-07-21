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
from backend.core.application.commands.membership_lifecycle import (
    ActivateMembershipCommand,
    DeactivateMembershipCommand,
)
from backend.core.application.policies.membership_administration import (
    ensure_not_self_deactivation,
    ensure_organization_retains_administrator,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.exceptions import MembershipAlreadyActive, MembershipAlreadyInactive
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class ActivateMembershipHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: ActivateMembershipCommand) -> Membership:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.MEMBERSHIP_ACTIVATE,
            context=audit_context,
            resource_type=AuditResourceType.MEMBERSHIP,
            resource_id=command.membership_id.value,
        )

        def operation() -> Membership:
            membership = self._unit_of_work.memberships.get(command.membership_id)
            if membership.status is MembershipStatus.ACTIVE:
                raise MembershipAlreadyActive(membership.id)
            now = datetime.now(UTC)
            return membership.model_copy(
                update={
                    "status": MembershipStatus.ACTIVE,
                    "joined_at": membership.joined_at or now,
                    "updated_at": now,
                    "revoked_at": None,
                }
            )

        def success_spec(membership: Membership) -> AuditRecordSpec:
            self._unit_of_work.memberships.save(membership)
            return AuditRecordSpec(
                action=AuditAction.MEMBERSHIP_ACTIVATE,
                context=audit_context,
                resource_type=AuditResourceType.MEMBERSHIP,
                resource_id=membership.id.value,
                target_organization_id=membership.organization_id,
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )


class DeactivateMembershipHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: DeactivateMembershipCommand) -> Membership:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.MEMBERSHIP_DEACTIVATE,
            context=audit_context,
            resource_type=AuditResourceType.MEMBERSHIP,
            resource_id=command.membership_id.value,
        )

        def operation() -> Membership:
            membership = self._unit_of_work.memberships.get(command.membership_id)
            if not membership.is_active():
                raise MembershipAlreadyInactive(membership.id)
            organization_memberships = tuple(
                self._unit_of_work.memberships.list_by_organization(membership.organization_id)
            )
            ensure_not_self_deactivation(membership, command.authorization)
            ensure_organization_retains_administrator(membership, organization_memberships)
            now = datetime.now(UTC)
            return membership.model_copy(
                update={
                    "status": MembershipStatus.REVOKED,
                    "updated_at": now,
                    "revoked_at": now,
                }
            )

        def success_spec(membership: Membership) -> AuditRecordSpec:
            self._unit_of_work.memberships.save(membership)
            return AuditRecordSpec(
                action=AuditAction.MEMBERSHIP_DEACTIVATE,
                context=audit_context,
                resource_type=AuditResourceType.MEMBERSHIP,
                resource_id=membership.id.value,
                target_organization_id=membership.organization_id,
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
