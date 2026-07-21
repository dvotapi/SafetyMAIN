from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import (
    get_authenticate_user_handler,
    get_refresh_authentication_handler,
)
from backend.api.openapi import AUTH_ERROR_RESPONSES, success_response
from backend.api.operation_ids import AUTH_LOGIN, AUTH_REFRESH
from backend.api.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.contracts.token_service import AuthenticationTokens


router = APIRouter(prefix="/auth", tags=["Authentication"])


def _to_token_response(tokens: AuthenticationTokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
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
    request: LoginRequest,
    handler: Annotated[AuthenticateUserHandler, Depends(get_authenticate_user_handler)],
) -> TokenResponse:
    tokens = handler.handle(
        AuthenticateUserCommand(
            email=request.email,
            password=request.password,
        )
    )
    return _to_token_response(tokens)


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
    request: RefreshTokenRequest,
    handler: Annotated[
        RefreshAuthenticationHandler,
        Depends(get_refresh_authentication_handler),
    ],
) -> TokenResponse:
    tokens = handler.handle(
        RefreshAuthenticationCommand(refresh_token=request.refresh_token)
    )
    return _to_token_response(tokens)
