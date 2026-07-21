from __future__ import annotations


class AuthenticationError(Exception):
    """Base class for application authentication errors."""


class UnauthenticatedError(AuthenticationError):
    """Raised when a request lacks valid authentication credentials."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when supplied credentials are invalid."""


class InvalidRefreshTokenError(AuthenticationError):
    """Raised when a refresh token is invalid or expired."""


class AuthenticationForbiddenError(AuthenticationError):
    """Raised when an authenticated identity is not permitted to sign in."""
