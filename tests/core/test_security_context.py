from __future__ import annotations

from uuid import uuid4

from backend.core.application.context.security_context import SecurityContext
from backend.core.domain.value_objects import OrganizationId, UserId


def test_security_context_supports_anonymous_requests() -> None:
    context = SecurityContext.anonymous(request_id="req-1")

    assert context.is_authenticated is False
    assert context.user_id is None
    assert context.organization_id is None
    assert context.actor_user_id is None


def test_security_context_carries_actor_and_organization() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())

    context = SecurityContext.authenticated(
        user_id=user_id,
        organization_id=organization_id,
        authentication_method="bearer_jwt",
        request_id="req-2",
    )

    assert context.is_authenticated is True
    assert context.actor_user_id == user_id
    assert context.organization_id == organization_id
    assert context.authentication_method == "bearer_jwt"
