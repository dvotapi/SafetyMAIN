from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from backend.core.domain.exceptions import (
    DuplicateMembership,
    DuplicateUserEmail,
    InvalidMembershipRole,
)
from backend.core.domain.value_objects import OrganizationId, UserId


def raise_mapped_identity_integrity_error(
    error: IntegrityError,
    *,
    email: str | None = None,
    user_id: UserId | None = None,
    organization_id: OrganizationId | None = None,
    role: str | None = None,
) -> None:
    """Re-raise known identity constraint failures as domain exceptions.

    Unrecognized integrity errors are re-raised unchanged for infrastructure
    diagnostics; API layers must not expose raw SQLAlchemy errors.
    """

    message = str(getattr(error, "orig", error)).lower()
    if "uq_users_email" in message:
        raise DuplicateUserEmail(email or "email") from error
    if "uq_memberships_user_organization" in message:
        if user_id is None or organization_id is None:
            raise error
        raise DuplicateMembership(
            user_id=user_id,
            organization_id=organization_id,
        ) from error
    if "ck_memberships_role_system" in message:
        raise InvalidMembershipRole(role or "unknown") from error
    raise error
