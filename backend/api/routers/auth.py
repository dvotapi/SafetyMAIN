from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from backend.api.authentication_audit import build_authentication_audit_context
from backend.api.dependencies import (
    get_authenticate_user_handler,
    get_auth_session_handler,
    get_authenticated_user,
    get_logout_handler,
    get_refresh_authentication_handler,
)
from backend.api.openapi import AUTH_ERROR_RESPONSES, success_response
from backend.api.operation_ids import AUTH_LOGIN, AUTH_LOGOUT, AUTH_REFRESH, AUTH_SESSION
from backend.api.schemas.auth import (
    AuthSessionMembership,
    AuthSessionResponse,
    AuthSessionUser,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.logout import LogoutCommand
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.get_auth_session import GetAuthSessionHandler
from backend.core.application.handlers.logout import LogoutHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.application.queries.get_auth_session import AuthSession, GetAuthSessionQuery
from backend.core.contracts.token_service import AuthenticationTokens
from backend.core.domain.value_objects import UserId

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _to_token_response(tokens: AuthenticationTokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


def _to_auth_session_response(session: AuthSession) -> AuthSessionResponse:
    return AuthSessionResponse(
        user=AuthSessionUser(
            id=session.user_id.value,
            email=session.email,
            display_name=session.display_name,
            status=session.status,
        ),
        memberships=[
            AuthSessionMembership(
                organization_id=membership.organization_id.value,
                organization_name=membership.organization_name,
                role=membership.role.value,
                status=membership.status.value,
                permissions=list(membership.permissions),
            )
            for membership in session.memberships
        ],
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    operation_id=AUTH_LOGIN,
    summary="Authenticate a platform user",
    responses={
        **success_response(model=TokenResponse, description="Authentication succeeded."),
        **AUTH_ERROR_RESPONSES,
    },
)
def login(
    request: Request,
    body: LoginRequest,
    handler: Annotated[AuthenticateUserHandler, Depends(get_authenticate_user_handler)],
) -> TokenResponse:
    tokens = handler.handle(
        AuthenticateUserCommand(
            email=body.email,
            password=body.password,
            audit_context=build_authentication_audit_context(request),
        )
    )
    return _to_token_response(tokens)


@router.get(
    "/session",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
    operation_id=AUTH_SESSION,
    summary="Bootstrap the authenticated session",
    responses={
        **success_response(
            model=AuthSessionResponse,
            description="Authenticated session context.",
        ),
        **AUTH_ERROR_RESPONSES,
    },
)
def get_session(
    user_id: Annotated[UserId, Depends(get_authenticated_user)],
    handler: Annotated[GetAuthSessionHandler, Depends(get_auth_session_handler)],
) -> AuthSessionResponse:
    session = handler.handle(GetAuthSessionQuery(user_id=user_id))
    return _to_auth_session_response(session)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    operation_id=AUTH_REFRESH,
    summary="Refresh authentication tokens",
    responses={
        **success_response(model=TokenResponse, description="Tokens were refreshed."),
        **AUTH_ERROR_RESPONSES,
    },
)
def refresh_tokens(
    request: Request,
    body: RefreshTokenRequest,
    handler: Annotated[
        RefreshAuthenticationHandler,
        Depends(get_refresh_authentication_handler),
    ],
) -> TokenResponse:
    tokens = handler.handle(
        RefreshAuthenticationCommand(
            refresh_token=body.refresh_token,
            audit_context=build_authentication_audit_context(request),
        )
    )
    return _to_token_response(tokens)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id=AUTH_LOGOUT,
    summary="Revoke the presented refresh session",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Logout completed."},
        **AUTH_ERROR_RESPONSES,
    },
)
def logout(
    request: Request,
    body: LogoutRequest,
    handler: Annotated[LogoutHandler, Depends(get_logout_handler)],
) -> Response:
    handler.handle(
        LogoutCommand(
            refresh_token=body.refresh_token,
            audit_context=build_authentication_audit_context(request),
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
