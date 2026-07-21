from __future__ import annotations

from backend.core.application.queries.invitations import ListInvitationsQuery
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects.invitation_list_criteria import (
    InvitationListCriteria,
    InvitationListResult,
)


class ListInvitationsHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, query: ListInvitationsQuery) -> InvitationListResult:
        criteria = InvitationListCriteria(
            organization_id=query.organization_id,
            offset=query.offset,
            limit=query.limit,
            as_of=self._clock.now(),
            email=query.email,
            role=query.role,
            status=query.status,
            sort_ascending=query.sort_ascending,
        )
        return self._unit_of_work.invitations.list_invitations(criteria)
