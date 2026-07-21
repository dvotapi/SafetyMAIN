from __future__ import annotations

from backend.core.application.queries.get_user import GetUserQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import User


class GetUserHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetUserQuery) -> User:
        return self._unit_of_work.users.get(query.user_id)
