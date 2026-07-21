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
from backend.core.application.audit.metadata import role_change_metadata
from backend.core.application.commands.update_membership_role import UpdateMembershipRoleCommand
from backend.core.application.policies.membership_administration import (
    ensure_not_self_role_downgrade,
    ensure_organization_retains_administrator,
    validate_membership_role,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class UpdateMembershipRoleHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: UpdateMembershipRoleCommand) -> Membership:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.MEMBERSHIP_ROLE_CHANGE,
            context=audit_context,
            resource_type=AuditResourceType.MEMBERSHIP,
            resource_id=command.membership_id.value,
        )

        def operation() -> tuple[Membership, str]:
            validate_membership_role(command.role)
            membership = self._unit_of_work.memberships.get(command.membership_id)
            previous_role = membership.role.value
            organization_memberships = tuple(
                self._unit_of_work.memberships.list_by_organization(membership.organization_id)
            )
            ensure_not_self_role_downgrade(
                membership,
                command.role,
                command.authorization,
            )
            if membership.role != command.role:
                ensure_organization_retains_administrator(membership, organization_memberships)
            updated_membership = membership.model_copy(
                update={"role": command.role, "updated_at": datetime.now(UTC)}
            )
            return updated_membership, previous_role

        def success_spec(result: tuple[Membership, str]) -> AuditRecordSpec:
            membership, previous_role = result
            self._unit_of_work.memberships.save(membership)
            return AuditRecordSpec(
                action=AuditAction.MEMBERSHIP_ROLE_CHANGE,
                context=audit_context,
                resource_type=AuditResourceType.MEMBERSHIP,
                resource_id=membership.id.value,
                target_organization_id=membership.organization_id,
                metadata=role_change_metadata(
                    previous_role=previous_role,
                    new_role=membership.role.value,
                ),
            )

        membership, _ = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return membership
