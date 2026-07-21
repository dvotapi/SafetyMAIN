from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import MembershipId


@dataclass(frozen=True, slots=True)
class GetMembershipQuery:
    membership_id: MembershipId
