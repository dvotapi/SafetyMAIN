from __future__ import annotations

from backend.core.application.queries.get_membership import GetMembershipQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.membership import Membership


class GetMembershipHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetMembershipQuery) -> Membership:
        return self._unit_of_work.memberships.get(query.membership_id)
