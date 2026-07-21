from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.invitation import Invitation


@dataclass(frozen=True, slots=True)
class InvitationWithTokenResult:
    invitation: Invitation
    token: str
