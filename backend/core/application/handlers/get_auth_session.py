from __future__ import annotations

from backend.core.application.queries.get_auth_session import (
    AuthSession,
    AuthSessionMembership,
    GetAuthSessionQuery,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import MembershipStatus
from backend.core.domain.value_objects.role_permissions import permissions_for_role


class GetAuthSessionHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetAuthSessionQuery) -> AuthSession:
        user = self._unit_of_work.users.get(query.user_id)
        memberships: list[AuthSessionMembership] = []

        for membership in self._unit_of_work.memberships.list_by_user(query.user_id):
            if membership.status is not MembershipStatus.ACTIVE:
                continue

            organization = self._unit_of_work.organizations.get(membership.organization_id)
            permissions = tuple(
                sorted(permission.value for permission in permissions_for_role(membership.role))
            )
            memberships.append(
                AuthSessionMembership(
                    organization_id=membership.organization_id,
                    organization_name=organization.name,
                    role=membership.role,
                    status=membership.status,
                    permissions=permissions,
                )
            )

        return AuthSession(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status.value,
            memberships=tuple(memberships),
        )
