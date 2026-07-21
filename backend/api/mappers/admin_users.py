from __future__ import annotations

from backend.api.schemas.admin_users import UserListResponse, UserResponse
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.user import User
from backend.core.domain.value_objects.user_list_criteria import UserListResult


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id.value,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active(),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_user_list_response(result: UserListResult) -> UserListResponse:
    return UserListResponse(
        items=[to_user_response(user) for user in result.items],
        pagination=PaginationResponse(
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        ),
    )
