from __future__ import annotations

from backend.api.schemas.admin_organizations import (
    OrganizationListResponse,
    OrganizationResponse,
)
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.organization import Organization
from backend.core.domain.value_objects.organization_list_criteria import OrganizationListResult


def to_organization_response(organization: Organization) -> OrganizationResponse:
    return OrganizationResponse(
        id=organization.id.value,
        name=organization.name,
        is_active=organization.is_active(),
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )


def to_organization_list_response(
    result: OrganizationListResult,
) -> OrganizationListResponse:
    return OrganizationListResponse(
        items=[to_organization_response(organization) for organization in result.items],
        pagination=PaginationResponse(
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        ),
    )
