from __future__ import annotations

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.exceptions.hazard import (
    DuplicateHazardCode,
    HazardNotFound,
    HazardVersionConflict,
)
from backend.core.domain.repositories.hazard_repository import HazardRepositoryContract
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.hazard_code import HazardCode
from backend.core.domain.value_objects.hazard_query import HazardPage, HazardQuery
from backend.core.domain.value_objects.safety_enums import HazardStatus
from backend.core.domain.value_objects.safety_ids import HazardId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.hazard_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.hazard_model import (
    HazardModel,
)


class SQLAlchemyHazardRepository(HazardRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, hazard: Hazard) -> None:
        existing = self.get_by_code(hazard.organization_id, hazard.code)
        if existing is not None:
            raise DuplicateHazardCode(
                organization_id=hazard.organization_id,
                code=hazard.code.value,
            )
        self._session.add(to_model(hazard))
        try:
            self._session.flush()
        except IntegrityError as error:
            if "uq_safety_hazards_organization_id_code" in str(error.orig):
                raise DuplicateHazardCode(
                    organization_id=hazard.organization_id,
                    code=hazard.code.value,
                ) from error
            raise

    def get(
        self,
        organization_id: OrganizationId,
        hazard_id: HazardId,
    ) -> Hazard | None:
        model = self._session.scalar(
            select(HazardModel).where(
                HazardModel.id == hazard_id.value,
                HazardModel.organization_id == organization_id.value,
            )
        )
        if model is None:
            return None
        return to_domain(model)

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: HazardCode,
    ) -> Hazard | None:
        model = self._session.scalar(
            select(HazardModel).where(
                HazardModel.organization_id == organization_id.value,
                HazardModel.code == code.value,
            )
        )
        if model is None:
            return None
        return to_domain(model)

    def list(self, query: HazardQuery) -> HazardPage:
        filters: list[object] = [
            HazardModel.organization_id == query.organization_id.value
        ]
        if not query.include_archived:
            filters.append(HazardModel.status != HazardStatus.ARCHIVED.value)
        if query.status is not None:
            filters.append(HazardModel.status == query.status.value)
        if query.category is not None:
            filters.append(HazardModel.category == query.category.value)
        if query.safety_direction is not None:
            filters.append(
                HazardModel.safety_directions.contains([query.safety_direction.value])
            )
        if query.source is not None:
            filters.append(HazardModel.source == query.source.value)
        if query.affected_subject is not None:
            filters.append(
                HazardModel.affected_subjects.contains([query.affected_subject.value])
            )
        if query.identified_from is not None:
            filters.append(HazardModel.identified_at >= query.identified_from)
        if query.identified_to is not None:
            filters.append(HazardModel.identified_at <= query.identified_to)
        if query.created_from is not None:
            filters.append(HazardModel.created_at >= query.created_from)
        if query.created_to is not None:
            filters.append(HazardModel.created_at <= query.created_to)
        if query.search is not None and query.search.strip():
            pattern = f"%{query.search.strip()}%"
            filters.append(
                or_(
                    HazardModel.code.ilike(pattern),
                    HazardModel.title.ilike(pattern),
                    HazardModel.description.ilike(pattern),
                )
            )

        where_clause = and_(*filters)
        total = self._session.scalar(
            select(func.count()).select_from(HazardModel).where(where_clause)
        )
        assert total is not None
        models = self._session.scalars(
            select(HazardModel)
            .where(where_clause)
            .order_by(HazardModel.created_at.desc(), HazardModel.id.desc())
            .offset(query.offset)
            .limit(query.limit)
        ).all()
        return HazardPage(
            items=tuple(to_domain(model) for model in models),
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def save(self, hazard: Hazard, *, expected_version: int) -> None:
        result = self._session.execute(
            update(HazardModel)
            .where(
                HazardModel.id == hazard.id.value,
                HazardModel.organization_id == hazard.organization_id.value,
                HazardModel.version == expected_version,
            )
            .values(
                code=hazard.code.value,
                title=hazard.title,
                description=hazard.description,
                category=hazard.category.value,
                safety_directions=[d.value for d in hazard.safety_directions],
                source=hazard.source.value,
                affected_subjects=[s.value for s in hazard.affected_subjects],
                location_reference=hazard.location_reference,
                process_reference=hazard.process_reference,
                equipment_reference=hazard.equipment_reference,
                extension_references=dict(hazard.extension_references),
                status=hazard.status.value,
                identified_at=hazard.identified_at,
                identified_by=hazard.identified_by.value,
                reviewed_at=hazard.reviewed_at,
                reviewed_by=(
                    None if hazard.reviewed_by is None else hazard.reviewed_by.value
                ),
                archived_at=hazard.archived_at,
                archived_by=(
                    None if hazard.archived_by is None else hazard.archived_by.value
                ),
                updated_at=hazard.updated_at,
                version=hazard.version,
            )
        )
        if result.rowcount == 0:
            existing = self.get(hazard.organization_id, hazard.id)
            if existing is None:
                raise HazardNotFound(hazard.id)
            raise HazardVersionConflict(
                hazard_id=hazard.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        # Keep identity map consistent for subsequent reads in the same UoW.
        model = self._session.get(HazardModel, hazard.id.value)
        if model is not None:
            apply_to_model(model, hazard)
