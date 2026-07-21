from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_activate_user_handler,
    get_create_user_handler,
    get_deactivate_user_handler,
    get_get_user_handler,
    get_list_users_handler,
    get_update_user_handler,
    get_user_id,
    require_permission,
)
from backend.api.mappers.admin_users import to_user_list_response, to_user_response
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    ACTIVATE_USER,
    CREATE_USER,
    DEACTIVATE_USER,
    GET_USER,
    LIST_USERS,
    UPDATE_USER,
)
from backend.api.schemas.admin_users import (
    CreateUserRequest,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from backend.api.security import TenantContext
from backend.core.application.authorization.policies.resource_permissions import (
    USER_READ,
    USER_WRITE,
)
from backend.core.application.commands.create_user import CreateUserCommand
from backend.core.application.commands.update_user import UpdateUserCommand
from backend.core.application.commands.user_lifecycle import (
    ActivateUserCommand,
    DeactivateUserCommand,
)
from backend.core.application.handlers.create_user import CreateUserHandler
from backend.core.application.handlers.get_user import GetUserHandler
from backend.core.application.handlers.list_users import ListUsersHandler
from backend.core.application.handlers.update_user import UpdateUserHandler
from backend.core.application.handlers.user_lifecycle import (
    ActivateUserHandler,
    DeactivateUserHandler,
)
from backend.core.application.queries.get_user import GetUserQuery
from backend.core.application.queries.list_users import ListUsersQuery
from backend.core.domain.value_objects import UserId

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_USER,
    summary="Create a user",
    responses={
        **created_response(model=UserResponse, description="User created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_user(
    request_body: CreateUserRequest,
    _tenant_context: Annotated[TenantContext, Depends(require_permission(USER_WRITE))],
    handler: Annotated[CreateUserHandler, Depends(get_create_user_handler)],
) -> JSONResponse:
    user = handler.handle(
        CreateUserCommand(
            email=request_body.email,
            display_name=request_body.display_name,
            is_active=request_body.is_active,
        )
    )
    response_body = to_user_response(user)
    location = f"{API_V1_PREFIX}/admin/users/{user.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=UserListResponse,
    operation_id=LIST_USERS,
    summary="List users",
    responses={
        **success_response(model=UserListResponse, description="Users returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_users(
    _tenant_context: Annotated[TenantContext, Depends(require_permission(USER_READ))],
    handler: Annotated[ListUsersHandler, Depends(get_list_users_handler)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    is_active: Annotated[bool | None, Query()] = None,
    email: Annotated[str | None, Query(max_length=320)] = None,
    display_name: Annotated[str | None, Query(max_length=255)] = None,
    sort_ascending: Annotated[bool, Query(alias="sort_asc")] = False,
) -> UserListResponse:
    result = handler.handle(
        ListUsersQuery(
            offset=offset,
            limit=limit,
            is_active=is_active,
            email=email,
            display_name=display_name,
            sort_ascending=sort_ascending,
        )
    )
    return to_user_list_response(result)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    operation_id=GET_USER,
    summary="Get a user",
    responses={
        **success_response(model=UserResponse, description="User returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_user(
    user_id: Annotated[UserId, Depends(get_user_id)],
    _tenant_context: Annotated[TenantContext, Depends(require_permission(USER_READ))],
    handler: Annotated[GetUserHandler, Depends(get_get_user_handler)],
) -> UserResponse:
    user = handler.handle(GetUserQuery(user_id=user_id))
    return to_user_response(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    operation_id=UPDATE_USER,
    summary="Update a user",
    responses={
        **success_response(model=UserResponse, description="User updated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_user(
    request_body: UpdateUserRequest,
    user_id: Annotated[UserId, Depends(get_user_id)],
    _tenant_context: Annotated[TenantContext, Depends(require_permission(USER_WRITE))],
    handler: Annotated[UpdateUserHandler, Depends(get_update_user_handler)],
) -> UserResponse:
    user = handler.handle(
        UpdateUserCommand(
            user_id=user_id,
            display_name=request_body.display_name,
            email=request_body.email,
            is_active=request_body.is_active,
        )
    )
    return to_user_response(user)


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    operation_id=ACTIVATE_USER,
    summary="Activate a user",
    responses={
        **success_response(model=UserResponse, description="User activated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def activate_user(
    user_id: Annotated[UserId, Depends(get_user_id)],
    _tenant_context: Annotated[TenantContext, Depends(require_permission(USER_WRITE))],
    handler: Annotated[ActivateUserHandler, Depends(get_activate_user_handler)],
) -> UserResponse:
    user = handler.handle(ActivateUserCommand(user_id=user_id))
    return to_user_response(user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    operation_id=DEACTIVATE_USER,
    summary="Deactivate a user",
    responses={
        **success_response(model=UserResponse, description="User deactivated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def deactivate_user(
    user_id: Annotated[UserId, Depends(get_user_id)],
    _tenant_context: Annotated[TenantContext, Depends(require_permission(USER_WRITE))],
    handler: Annotated[DeactivateUserHandler, Depends(get_deactivate_user_handler)],
) -> UserResponse:
    user = handler.handle(DeactivateUserCommand(user_id=user_id))
    return to_user_response(user)
