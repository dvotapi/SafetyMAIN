from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.commands.update_membership_role import UpdateMembershipRoleCommand
from backend.core.application.policies.membership_administration import (
    ensure_not_self_role_downgrade,
    ensure_organization_retains_administrator,
    validate_membership_role,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership


class UpdateMembershipRoleHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: UpdateMembershipRoleCommand) -> Membership:
        validate_membership_role(command.role)

        membership = self._unit_of_work.memberships.get(command.membership_id)
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

        now = datetime.now(UTC)
        updated_membership = membership.model_copy(
            update={
                "role": command.role,
                "updated_at": now,
            }
        )
        self._unit_of_work.memberships.save(updated_membership)
        self._unit_of_work.commit()
        return updated_membership
