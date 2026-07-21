from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.membership import Membership
from backend.core.domain.exceptions import (
    LastOrganizationAdministratorError,
    SelfMembershipDeactivationError,
    SelfMembershipRoleDowngradeError,
)
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.domain.value_objects.role import SystemRole


@dataclass(frozen=True, slots=True)
class MembershipAuthorizationContext:
    actor_user_id: UserId
    authorization_organization_id: OrganizationId
    authorization_membership_id: MembershipId


def validate_membership_role(role: Role) -> None:
    try:
        SystemRole(role.value)
    except ValueError as exc:
        from backend.core.domain.exceptions import InvalidMembershipRole

        raise InvalidMembershipRole(role.value) from exc


def is_admin_role(role: Role) -> bool:
    return role.value == SystemRole.ADMIN.value


def count_active_administrators(memberships: tuple[Membership, ...]) -> int:
    return sum(
        1
        for membership in memberships
        if membership.is_active() and is_admin_role(membership.role)
    )


def ensure_not_self_deactivation(
    membership: Membership,
    authorization: MembershipAuthorizationContext,
) -> None:
    if membership.id == authorization.authorization_membership_id:
        raise SelfMembershipDeactivationError(membership.id)


def ensure_not_self_role_downgrade(
    membership: Membership,
    new_role: Role,
    authorization: MembershipAuthorizationContext,
) -> None:
    if membership.id != authorization.authorization_membership_id:
        return
    if is_admin_role(membership.role) and not is_admin_role(new_role):
        raise SelfMembershipRoleDowngradeError(membership.id)


def ensure_organization_retains_administrator(
    membership: Membership,
    organization_memberships: tuple[Membership, ...],
) -> None:
    if not membership.is_active() or not is_admin_role(membership.role):
        return
    if count_active_administrators(organization_memberships) <= 1:
        raise LastOrganizationAdministratorError(membership.organization_id)
