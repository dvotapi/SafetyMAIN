from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.shelf_section import ShelfSection
from backend.core.domain.exceptions.shelf import (
    DuplicateShelfSectionCode,
    DuplicateShelfSectionNumber,
    ShelfSectionNotFound,
    ShelfSectionVersionConflict,
)
from backend.core.domain.repositories.shelf_section_repository import (
    ShelfSectionRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import ShelfSectionId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.shelf_mapper import (
    section_to_domain,
    section_to_model,
    subsection_to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.shelf_model import (
    ShelfSectionModel,
    ShelfSubsectionModel,
)


class SQLAlchemyShelfSectionRepository(ShelfSectionRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, section: ShelfSection) -> None:
        self._assert_unique(section)
        self._session.add(section_to_model(section))
        self._session.flush()
        for subsection in section.subsections:
            self._session.add(subsection_to_model(section, subsection))
        self._flush(section)

    def get(
        self, organization_id: OrganizationId, section_id: ShelfSectionId
    ) -> ShelfSection | None:
        return self._one(
            ShelfSectionModel.organization_id == organization_id.value,
            ShelfSectionModel.id == section_id.value,
        )

    def get_by_code(self, organization_id: OrganizationId, code: str) -> ShelfSection | None:
        return self._one(
            ShelfSectionModel.organization_id == organization_id.value,
            ShelfSectionModel.code == code,
        )

    def list(self, organization_id: OrganizationId) -> tuple[ShelfSection, ...]:
        models = self._session.scalars(
            select(ShelfSectionModel)
            .where(ShelfSectionModel.organization_id == organization_id.value)
            .order_by(ShelfSectionModel.number)
        ).all()
        return self._hydrate(models)

    def save(self, section: ShelfSection, *, expected_version: int) -> None:
        result = self._session.execute(
            update(ShelfSectionModel)
            .where(
                ShelfSectionModel.id == section.id.value,
                ShelfSectionModel.organization_id == section.organization_id.value,
                ShelfSectionModel.version == expected_version,
            )
            .values(
                number=section.number,
                title=section.title,
                safety_domain=section.safety_domain.value,
                updated_at=section.updated_at,
                version=section.version,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            stored = self._session.scalar(
                select(ShelfSectionModel.version).where(
                    ShelfSectionModel.id == section.id.value,
                    ShelfSectionModel.organization_id == section.organization_id.value,
                )
            )
            if stored is None:
                raise ShelfSectionNotFound(section.id)
            raise ShelfSectionVersionConflict(
                section_id=section.id,
                expected_version=expected_version,
                actual_version=stored,
            )
        stored_subsections = {
            row.id: row
            for row in self._session.scalars(
                select(ShelfSubsectionModel).where(
                    ShelfSubsectionModel.section_id == section.id.value
                )
            ).all()
        }
        for subsection in section.subsections:
            row = stored_subsections.get(subsection.id.value)
            if row is None:
                self._session.add(subsection_to_model(section, subsection))
            elif row.title != subsection.title:
                row.title = subsection.title
        self._flush(section)

    def _one(self, *criteria: ColumnElement[bool]) -> ShelfSection | None:
        model = self._session.scalar(select(ShelfSectionModel).where(*criteria))
        if model is None:
            return None
        return self._hydrate([model])[0]

    def _hydrate(self, models: Sequence[ShelfSectionModel]) -> tuple[ShelfSection, ...]:
        if not models:
            return ()
        grouped: dict[UUID, list[ShelfSubsectionModel]] = {model.id: [] for model in models}
        for row in self._session.scalars(
            select(ShelfSubsectionModel).where(
                ShelfSubsectionModel.section_id.in_(list(grouped))
            )
        ).all():
            grouped[row.section_id].append(row)
        return tuple(section_to_domain(model, grouped[model.id]) for model in models)

    def _assert_unique(self, section: ShelfSection) -> None:
        clash = self._session.execute(
            select(ShelfSectionModel.code, ShelfSectionModel.number).where(
                ShelfSectionModel.organization_id == section.organization_id.value,
                (ShelfSectionModel.code == section.code)
                | (ShelfSectionModel.number == section.number),
            )
        ).first()
        if clash is None:
            return
        if clash.code == section.code:
            raise DuplicateShelfSectionCode(
                organization_id=section.organization_id, code=section.code
            )
        raise DuplicateShelfSectionNumber(
            organization_id=section.organization_id, number=section.number
        )

    def _flush(self, section: ShelfSection) -> None:
        try:
            self._session.flush()
        except IntegrityError as error:
            message = str(error.orig)
            if "uq_shelf_sections_organization_id_code" in message:
                raise DuplicateShelfSectionCode(
                    organization_id=section.organization_id, code=section.code
                ) from error
            if "uq_shelf_sections_organization_id_number" in message:
                raise DuplicateShelfSectionNumber(
                    organization_id=section.organization_id, number=section.number
                ) from error
            raise
