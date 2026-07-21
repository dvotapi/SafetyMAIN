from __future__ import annotations

from datetime import UTC, datetime

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.sqlalchemy.models.membership_model import (
    MembershipModel,
)


def to_model(membership: Membership) -> MembershipModel:
    now = datetime.now(UTC)
    return MembershipModel(
        id=membership.id.value,
        user_id=membership.user_id.value,
        organization_id=membership.organization_id.value,
        role=membership.role.value,
        is_active=membership.is_active(),
        created_at=membership.joined_at or now,
        updated_at=membership.updated_at,
    )


def apply_to_model(model: MembershipModel, membership: Membership) -> None:
    model.role = membership.role.value
    model.is_active = membership.is_active()
    model.updated_at = membership.updated_at


def to_domain(model: MembershipModel) -> Membership:
    status = MembershipStatus.ACTIVE if model.is_active else MembershipStatus.REVOKED
    return Membership(
        id=MembershipId(value=model.id),
        user_id=UserId(value=model.user_id),
        organization_id=OrganizationId(value=model.organization_id),
        status=status,
        role=Role(value=model.role),
        joined_at=model.created_at,
        updated_at=model.updated_at,
        revoked_at=None if model.is_active else model.updated_at,
    )
