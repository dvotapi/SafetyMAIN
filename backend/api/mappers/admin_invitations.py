from __future__ import annotations

from datetime import datetime

from backend.api.schemas.admin_invitations import (
    CreateInvitationResponse,
    InvitationListResponse,
    InvitationResponse,
    ReissueInvitationResponse,
)
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.invitation import Invitation
from backend.core.domain.value_objects.invitation_list_criteria import InvitationListResult


def to_invitation_response(invitation: Invitation, *, now: datetime) -> InvitationResponse:
    return InvitationResponse(
        id=invitation.id.value,
        organization_id=invitation.organization_id.value,
        email=invitation.email,
        role=invitation.role.value,
        status=invitation.effective_status(now=now).value,
        expires_at=invitation.expires_at,
        created_by=invitation.created_by.value,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        accepted_at=invitation.accepted_at,
        revoked_at=invitation.revoked_at,
    )


def to_create_invitation_response(
    invitation: Invitation,
    *,
    token: str,
    now: datetime,
) -> CreateInvitationResponse:
    return CreateInvitationResponse(
        invitation=to_invitation_response(invitation, now=now),
        token=token,
    )


def to_reissue_invitation_response(
    invitation: Invitation,
    *,
    token: str,
    now: datetime,
) -> ReissueInvitationResponse:
    return ReissueInvitationResponse(
        invitation=to_invitation_response(invitation, now=now),
        token=token,
    )


def to_invitation_list_response(
    result: InvitationListResult,
    *,
    now: datetime,
) -> InvitationListResponse:
    return InvitationListResponse(
        items=[to_invitation_response(invitation, now=now) for invitation in result.items],
        pagination=PaginationResponse(
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        ),
    )
