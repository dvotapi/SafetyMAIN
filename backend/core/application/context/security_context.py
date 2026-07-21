from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import OrganizationId, UserId


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Transport-free authenticated identity for Application use cases."""

    is_authenticated: bool = False
    user_id: UserId | None = None
    organization_id: OrganizationId | None = None
    authentication_method: str | None = None
    request_id: str | None = None

    @classmethod
    def anonymous(cls, *, request_id: str | None = None) -> SecurityContext:
        return cls(is_authenticated=False, request_id=request_id)

    @classmethod
    def authenticated(
        cls,
        *,
        user_id: UserId,
        organization_id: OrganizationId | None = None,
        authentication_method: str = "bearer_jwt",
        request_id: str | None = None,
    ) -> SecurityContext:
        return cls(
            is_authenticated=True,
            user_id=user_id,
            organization_id=organization_id,
            authentication_method=authentication_method,
            request_id=request_id,
        )

    @property
    def actor_user_id(self) -> UserId | None:
        return self.user_id if self.is_authenticated else None

    def with_organization(self, organization_id: OrganizationId) -> SecurityContext:
        return SecurityContext(
            is_authenticated=self.is_authenticated,
            user_id=self.user_id,
            organization_id=organization_id,
            authentication_method=self.authentication_method,
            request_id=self.request_id,
        )
