from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.create_membership import CreateMembershipCommand
from backend.core.application.policies.membership_administration import validate_membership_role
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.exceptions import DuplicateMembership
from backend.core.domain.value_objects import MembershipId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class CreateMembershipHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: CreateMembershipCommand) -> Membership:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.MEMBERSHIP_CREATE,
            context=audit_context,
            resource_type=AuditResourceType.MEMBERSHIP,
            target_organization_id=command.organization_id,
        )

        def operation() -> Membership:
            validate_membership_role(command.role)
            self._unit_of_work.users.get(command.user_id)
            self._unit_of_work.organizations.get(command.organization_id)
            if (
                self._unit_of_work.memberships.get_by_user_and_organization(
                    command.user_id,
                    command.organization_id,
                )
                is not None
            ):
                raise DuplicateMembership(
                    user_id=command.user_id,
                    organization_id=command.organization_id,
                )
            now = datetime.now(UTC)
            return Membership(
                id=MembershipId(value=uuid4()),
                user_id=command.user_id,
                organization_id=command.organization_id,
                status=(
                    MembershipStatus.ACTIVE if command.is_active else MembershipStatus.REVOKED
                ),
                role=command.role,
                joined_at=now,
                updated_at=now,
                revoked_at=None if command.is_active else now,
            )

        def success_spec(membership: Membership) -> AuditRecordSpec:
            self._unit_of_work.memberships.add(membership)
            return AuditRecordSpec(
                action=AuditAction.MEMBERSHIP_CREATE,
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
