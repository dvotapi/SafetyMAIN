from __future__ import annotations

from datetime import UTC, datetime

from backend.core.domain.entities.organization import Organization
from backend.core.domain.value_objects import OrganizationId
from backend.core.infrastructure.persistence.sqlalchemy.models.organization_model import (
    OrganizationModel,
)


def to_model(organization: Organization) -> OrganizationModel:
    now = datetime.now(UTC)
    return OrganizationModel(
        id=organization.id.value,
        name=organization.name,
        created_at=organization.created_at,
        updated_at=now,
    )


def apply_to_model(model: OrganizationModel, organization: Organization) -> None:
    model.name = organization.name
    model.updated_at = datetime.now(UTC)


def to_domain(model: OrganizationModel) -> Organization:
    return Organization(
        id=OrganizationId(value=model.id),
        name=model.name,
        created_at=model.created_at,
    )
