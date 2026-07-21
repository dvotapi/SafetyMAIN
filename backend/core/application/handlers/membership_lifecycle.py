from __future__ import annotations

from datetime import UTC, datetime

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


class ActivateMembershipHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: ActivateMembershipCommand) -> Membership:
        membership = self._unit_of_work.memberships.get(command.membership_id)
        if membership.status is MembershipStatus.ACTIVE:
            raise MembershipAlreadyActive(membership.id)

        now = datetime.now(UTC)
        updated_membership = membership.model_copy(
            update={
                "status": MembershipStatus.ACTIVE,
                "joined_at": membership.joined_at or now,
                "updated_at": now,
                "revoked_at": None,
            }
        )
        self._unit_of_work.memberships.save(updated_membership)
        self._unit_of_work.commit()
        return updated_membership


class DeactivateMembershipHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: DeactivateMembershipCommand) -> Membership:
        membership = self._unit_of_work.memberships.get(command.membership_id)
        if not membership.is_active():
            raise MembershipAlreadyInactive(membership.id)

        organization_memberships = tuple(
            self._unit_of_work.memberships.list_by_organization(membership.organization_id)
        )
        ensure_not_self_deactivation(membership, command.authorization)
        ensure_organization_retains_administrator(membership, organization_memberships)

        now = datetime.now(UTC)
        updated_membership = membership.model_copy(
            update={
                "status": MembershipStatus.REVOKED,
                "updated_at": now,
                "revoked_at": now,
            }
        )
        self._unit_of_work.memberships.save(updated_membership)
        self._unit_of_work.commit()
        return updated_membership
