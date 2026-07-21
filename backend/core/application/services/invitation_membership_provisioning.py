from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from backend.core.application.policies.membership_administration import validate_membership_role
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.exceptions import OrganizationAlreadyInactive
from backend.core.domain.exceptions.invitation import ExistingActiveMembership
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId


def provision_membership_for_invitation(
    unit_of_work: UnitOfWorkContract,
    *,
    user_id: UserId,
    organization_id: OrganizationId,
    role: Role,
    now: datetime,
) -> Membership:
    organization = unit_of_work.organizations.get(organization_id)
    if not organization.is_active():
        raise OrganizationAlreadyInactive(organization.id)

    existing_membership = unit_of_work.memberships.get_by_user_and_organization(
        user_id,
        organization_id,
    )
    if existing_membership is not None:
        if existing_membership.is_active():
            raise ExistingActiveMembership(
                user_id=user_id,
                organization_id=organization_id,
            )
        updated_membership = existing_membership.model_copy(
            update={
                "status": MembershipStatus.ACTIVE,
                "role": role,
                "joined_at": existing_membership.joined_at or now,
                "updated_at": now,
                "revoked_at": None,
            }
        )
        validate_membership_role(updated_membership.role)
        unit_of_work.memberships.save(updated_membership)
        return updated_membership

    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=user_id,
        organization_id=organization_id,
        status=MembershipStatus.ACTIVE,
        role=role,
        joined_at=now,
        updated_at=now,
        revoked_at=None,
    )
    validate_membership_role(membership.role)
    unit_of_work.memberships.add(membership)
    return membership


def default_invitation_expiration(*, now: datetime, ttl_days: int) -> datetime:
    return now + timedelta(days=ttl_days)
