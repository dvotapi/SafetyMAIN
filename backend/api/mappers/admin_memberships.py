from __future__ import annotations

from backend.api.schemas.admin_memberships import MembershipListResponse, MembershipResponse
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects.membership_list_criteria import MembershipListResult


def to_membership_response(membership: Membership) -> MembershipResponse:
    created_at = membership.joined_at or membership.updated_at
    return MembershipResponse(
        id=membership.id.value,
        organization_id=membership.organization_id.value,
        user_id=membership.user_id.value,
        role=membership.role.value,
        is_active=membership.is_active(),
        created_at=created_at,
        updated_at=membership.updated_at,
    )


def to_membership_list_response(result: MembershipListResult) -> MembershipListResponse:
    return MembershipListResponse(
        items=[to_membership_response(membership) for membership in result.items],
        pagination=PaginationResponse(
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        ),
    )
