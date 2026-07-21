from __future__ import annotations

from sqlalchemy.orm import Session

from backend.core.domain.entities.organization import Organization
from backend.core.domain.exceptions import OrganizationNotFound
from backend.core.domain.repositories import OrganizationRepositoryContract
from backend.core.domain.value_objects import OrganizationId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.organization_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.organization_model import (
    OrganizationModel,
)


class SQLAlchemyOrganizationRepository(OrganizationRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, organization: Organization) -> None:
        self._session.add(to_model(organization))

    def get(self, organization_id: OrganizationId) -> Organization:
        model = self._session.get(OrganizationModel, organization_id.value)
        if model is None:
            raise OrganizationNotFound(organization_id)
        return to_domain(model)

    def save(self, organization: Organization) -> None:
        model = self._session.get(OrganizationModel, organization.id.value)
        if model is None:
            raise OrganizationNotFound(organization.id)
        apply_to_model(model, organization)
