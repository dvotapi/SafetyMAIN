from __future__ import annotations

from backend.core.domain.entities.invitation import Invitation, InvitationStatus
from backend.core.domain.value_objects import InvitationId, OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.sqlalchemy.models.invitation_model import (
    InvitationModel,
)


def to_model(invitation: Invitation) -> InvitationModel:
    return InvitationModel(
        id=invitation.id.value,
        organization_id=invitation.organization_id.value,
        email=invitation.email,
        role=invitation.role.value,
        status=invitation.status.value,
        token_hash=invitation.token_hash,
        expires_at=invitation.expires_at,
        created_by=invitation.created_by.value,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        accepted_at=invitation.accepted_at,
        revoked_at=invitation.revoked_at,
    )


def apply_to_model(model: InvitationModel, invitation: Invitation) -> None:
    model.email = invitation.email
    model.role = invitation.role.value
    model.status = invitation.status.value
    model.token_hash = invitation.token_hash
    model.expires_at = invitation.expires_at
    model.updated_at = invitation.updated_at
    model.accepted_at = invitation.accepted_at
    model.revoked_at = invitation.revoked_at


def to_domain(model: InvitationModel) -> Invitation:
    return Invitation(
        id=InvitationId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        email=model.email,
        role=Role(value=model.role),
        status=InvitationStatus(model.status),
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        created_by=UserId(value=model.created_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        accepted_at=model.accepted_at,
        revoked_at=model.revoked_at,
    )
