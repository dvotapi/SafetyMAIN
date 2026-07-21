from __future__ import annotations

from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.exceptions.authentication import InvalidRefreshTokenError
from backend.core.contracts.token_service import (
    AuthenticationTokens,
    TokenServiceContract,
    TokenValidationError,
)


class RefreshAuthenticationHandler:
    def __init__(self, token_service: TokenServiceContract) -> None:
        self._token_service = token_service

    def handle(self, command: RefreshAuthenticationCommand) -> AuthenticationTokens:
        try:
            return self._token_service.refresh_tokens(command.refresh_token)
        except TokenValidationError as exc:
            raise InvalidRefreshTokenError() from exc
