from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.commands.create_membership import CreateMembershipCommand
from backend.core.application.policies.membership_administration import validate_membership_role
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.exceptions import DuplicateMembership
from backend.core.domain.value_objects import MembershipId


class CreateMembershipHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, command: CreateMembershipCommand) -> Membership:
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
        membership = Membership(
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
        self._unit_of_work.memberships.add(membership)
        self._unit_of_work.commit()
        return membership
