from __future__ import annotations

from backend.core.application.queries.list_users import ListUsersQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects.user_list_criteria import (
    UserListCriteria,
    UserListResult,
)


class ListUsersHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListUsersQuery) -> UserListResult:
        criteria = UserListCriteria(
            offset=query.offset,
            limit=query.limit,
            is_active=query.is_active,
            email=query.email,
            display_name=query.display_name,
            sort_ascending=query.sort_ascending,
        )
        return self._unit_of_work.users.list_users(criteria)
