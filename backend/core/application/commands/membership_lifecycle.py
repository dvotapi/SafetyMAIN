from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.policies.membership_administration import (
    MembershipAuthorizationContext,
)
from backend.core.domain.value_objects import MembershipId


@dataclass(frozen=True, slots=True)
class ActivateMembershipCommand:
    membership_id: MembershipId


@dataclass(frozen=True, slots=True)
class DeactivateMembershipCommand:
    membership_id: MembershipId
    authorization: MembershipAuthorizationContext
