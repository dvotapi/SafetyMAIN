from __future__ import annotations

from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.exceptions.authentication import (
    AuthenticationForbiddenError,
    InvalidCredentialsError,
)
from backend.core.contracts.password_hasher import PasswordHasherContract
from backend.core.contracts.token_service import AuthenticationTokens, TokenServiceContract
from backend.core.contracts.user_credentials import UserCredentialsPort
from backend.core.contracts.user_lookup import UserLookupPort


class AuthenticateUserHandler:
    def __init__(
        self,
        user_lookup: UserLookupPort,
        user_credentials: UserCredentialsPort,
        password_hasher: PasswordHasherContract,
        token_service: TokenServiceContract,
    ) -> None:
        self._user_lookup = user_lookup
        self._user_credentials = user_credentials
        self._password_hasher = password_hasher
        self._token_service = token_service

    def handle(self, command: AuthenticateUserCommand) -> AuthenticationTokens:
        normalized_email = command.email.strip().lower()
        user = self._user_lookup.get_user_by_email(normalized_email)
        if user is None:
            raise InvalidCredentialsError()

        if not user.can_authenticate():
            raise AuthenticationForbiddenError()

        password_hash = self._user_credentials.get_password_hash(user.id)
        if password_hash is None or not self._password_hasher.verify_password(
            command.password,
            password_hash,
        ):
            raise InvalidCredentialsError()

        return self._token_service.issue_tokens(user.id)
