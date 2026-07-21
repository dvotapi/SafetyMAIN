from __future__ import annotations

from backend.core.application.policies.membership_administration import validate_membership_role
from backend.core.application.queries.list_memberships import ListMembershipsQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects.membership_list_criteria import (
    MembershipListCriteria,
    MembershipListResult,
)


class ListMembershipsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListMembershipsQuery) -> MembershipListResult:
        if query.role is not None:
            validate_membership_role(query.role)
        criteria = MembershipListCriteria(
            organization_id=query.organization_id,
            offset=query.offset,
            limit=query.limit,
            user_id=query.user_id,
            role=query.role,
            is_active=query.is_active,
            sort_ascending=query.sort_ascending,
        )
        return self._unit_of_work.memberships.list_memberships(criteria)
