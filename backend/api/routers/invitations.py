from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import (
    get_accept_invitation_handler,
    get_authenticated_user,
    get_clock,
)
from backend.api.mappers.admin_invitations import to_invitation_response
from backend.api.openapi import PROTECTED_BUSINESS_ERROR_RESPONSES, success_response
from backend.api.operation_ids import ACCEPT_INVITATION
from backend.api.schemas.admin_invitations import AcceptInvitationRequest, InvitationResponse
from backend.core.application.commands.invitation_lifecycle import AcceptInvitationCommand
from backend.core.application.handlers.invitation_lifecycle import AcceptInvitationHandler
from backend.core.contracts.clock import ClockContract
from backend.core.domain.value_objects import UserId

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post(
    "/accept",
    response_model=InvitationResponse,
    operation_id=ACCEPT_INVITATION,
    summary="Accept an invitation",
    responses={
        **success_response(model=InvitationResponse, description="Invitation accepted."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
    status_code=status.HTTP_200_OK,
)
def accept_invitation(
    request_body: AcceptInvitationRequest,
    accepting_user_id: Annotated[UserId, Depends(get_authenticated_user)],
    handler: Annotated[AcceptInvitationHandler, Depends(get_accept_invitation_handler)],
    clock: Annotated[ClockContract, Depends(get_clock)],
) -> InvitationResponse:
    invitation = handler.handle(
        AcceptInvitationCommand(
            token=request_body.token,
            accepting_user_id=accepting_user_id,
        )
    )
    return to_invitation_response(invitation, now=clock.now())
