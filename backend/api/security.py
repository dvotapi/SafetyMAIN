from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Immutable authenticated identity for a single HTTP request."""

    user_id: UserId
    authentication_method: str = "bearer_jwt"
    request_id: str | None = None
