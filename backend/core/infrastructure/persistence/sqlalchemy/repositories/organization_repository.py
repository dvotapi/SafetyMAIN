from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.domain.entities.organization import Organization
from backend.core.domain.exceptions import OrganizationNotFound
from backend.core.domain.repositories import OrganizationRepositoryContract
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.organization_list_criteria import (
    OrganizationListCriteria,
    OrganizationListResult,
)
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

    def get_by_normalized_name(self, normalized_name: str) -> Organization | None:
        key = normalized_name.strip().casefold()
        statement = select(OrganizationModel).where(
            func.lower(OrganizationModel.name) == key
        )
        model = self._session.scalar(statement)
        if model is None:
            return None
        return to_domain(model)

    def save(self, organization: Organization) -> None:
        model = self._session.get(OrganizationModel, organization.id.value)
        if model is None:
            raise OrganizationNotFound(organization.id)
        apply_to_model(model, organization)

    def list_organizations(
        self,
        criteria: OrganizationListCriteria,
    ) -> OrganizationListResult:
        filters: list[object] = []
        if criteria.is_active is not None:
            filters.append(OrganizationModel.is_active == criteria.is_active)
        if criteria.name is not None:
            filters.append(
                OrganizationModel.name.ilike(f"%{criteria.name.strip()}%")
            )

        count_statement = select(func.count()).select_from(OrganizationModel)
        if filters:
            count_statement = count_statement.where(*filters)
        total = int(self._session.scalar(count_statement) or 0)

        statement = select(OrganizationModel)
        if filters:
            statement = statement.where(*filters)
        if criteria.sort_ascending:
            order_clause = (
                OrganizationModel.created_at.asc(),
                OrganizationModel.id.asc(),
            )
        else:
            order_clause = (
                OrganizationModel.created_at.desc(),
                OrganizationModel.id.asc(),
            )
        models = self._session.scalars(
            statement.order_by(*order_clause)
            .offset(criteria.offset)
            .limit(criteria.limit)
        ).all()

        return OrganizationListResult(
            items=tuple(to_domain(model) for model in models),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )
