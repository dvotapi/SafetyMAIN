from __future__ import annotations

from backend.core.application.queries.invitations import GetInvitationQuery
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.invitation import Invitation


class GetInvitationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, query: GetInvitationQuery) -> Invitation:
        return self._unit_of_work.invitations.get(query.invitation_id)
