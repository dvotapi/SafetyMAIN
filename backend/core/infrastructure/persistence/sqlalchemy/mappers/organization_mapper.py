from __future__ import annotations

from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.value_objects import OrganizationId
from backend.core.infrastructure.persistence.sqlalchemy.models.organization_model import (
    OrganizationModel,
)


def to_model(organization: Organization) -> OrganizationModel:
    return OrganizationModel(
        id=organization.id.value,
        name=organization.name,
        is_active=organization.is_active(),
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )


def apply_to_model(model: OrganizationModel, organization: Organization) -> None:
    model.name = organization.name
    model.is_active = organization.is_active()
    model.updated_at = organization.updated_at


def to_domain(model: OrganizationModel) -> Organization:
    return Organization(
        id=OrganizationId(value=model.id),
        name=model.name,
        status=(
            OrganizationStatus.ACTIVE if model.is_active else OrganizationStatus.DEACTIVATED
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
