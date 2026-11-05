from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, delete, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.exceptions.shelf import (
    DuplicateShelfSlotCode,
    ShelfSlotNotFound,
    ShelfSlotVersionConflict,
)
from backend.core.domain.repositories.shelf_slot_repository import (
    ShelfSlotRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSectionId,
    ShelfSlotId,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.shelf_mapper import (
    slot_columns,
    slot_to_domain,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.shelf_model import (
    ShelfSlotDocumentModel,
    ShelfSlotModel,
)

# Columns fixed at creation; never part of an UPDATE.
_IMMUTABLE = frozenset(
    {"id", "organization_id", "code", "section_id", "subsection_id", "created_at", "created_by"}
)


def _like_pattern(needle: str) -> str:
    escaped = needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class SQLAlchemyShelfSlotRepository(ShelfSlotRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, slot: ShelfSlot) -> None:
        if self.get_by_code(slot.organization_id, slot.code.value) is not None:
            raise DuplicateShelfSlotCode(
                organization_id=slot.organization_id, code=slot.code.value
            )
        self._session.add(ShelfSlotModel(**slot_columns(slot)))
        try:
            self._session.flush()
        except IntegrityError as error:
            if "uq_shelf_slots_organization_id_code" in str(error.orig):
                raise DuplicateShelfSlotCode(
                    organization_id=slot.organization_id, code=slot.code.value
                ) from error
            raise
        self._insert_links(slot, slot.linked_document_ids, first_position=0)

    def get(self, organization_id: OrganizationId, slot_id: ShelfSlotId) -> ShelfSlot | None:
        found = self._select(ShelfSlotModel.id == slot_id.value, organization_id=organization_id)
        return found[0] if found else None

    def get_by_code(self, organization_id: OrganizationId, code: str) -> ShelfSlot | None:
        found = self._select(ShelfSlotModel.code == code, organization_id=organization_id)
        return found[0] if found else None

    def list_by_section(
        self, organization_id: OrganizationId, section_id: ShelfSectionId
    ) -> tuple[ShelfSlot, ...]:
        return self._select(
            ShelfSlotModel.section_id == section_id.value, organization_id=organization_id
        )

    def list_all(self, organization_id: OrganizationId) -> tuple[ShelfSlot, ...]:
        return self._select(organization_id=organization_id)

    def search(
        self, organization_id: OrganizationId, query: str, *, limit: int
    ) -> tuple[ShelfSlot, ...]:
        needle = query.strip()
        if not needle:
            return ()
        pattern = _like_pattern(needle)
        return self._select(
            or_(
                ShelfSlotModel.code.ilike(pattern, escape="\\"),
                ShelfSlotModel.title.ilike(pattern, escape="\\"),
                ShelfSlotModel.short_title.ilike(pattern, escape="\\"),
            ),
            organization_id=organization_id,
            limit=limit,
        )

    def list_by_document(
        self, organization_id: OrganizationId, document_id: ComplianceDocumentId
    ) -> tuple[ShelfSlot, ...]:
        linked = select(ShelfSlotDocumentModel.slot_id).where(
            ShelfSlotDocumentModel.organization_id == organization_id.value,
            ShelfSlotDocumentModel.document_id == document_id.value,
        )
        return self._select(ShelfSlotModel.id.in_(linked), organization_id=organization_id)

    def save(self, slot: ShelfSlot, *, expected_version: int) -> None:
        values = {k: v for k, v in slot_columns(slot).items() if k not in _IMMUTABLE}
        result = self._session.execute(
            update(ShelfSlotModel)
            .where(
                ShelfSlotModel.id == slot.id.value,
                ShelfSlotModel.organization_id == slot.organization_id.value,
                ShelfSlotModel.version == expected_version,
            )
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            stored = self._session.scalar(
                select(ShelfSlotModel.version).where(
                    ShelfSlotModel.id == slot.id.value,
                    ShelfSlotModel.organization_id == slot.organization_id.value,
                )
            )
            if stored is None:
                raise ShelfSlotNotFound(slot.id)
            raise ShelfSlotVersionConflict(
                slot_id=slot.id, expected_version=expected_version, actual_version=stored
            )
        self._sync_links(slot)

    # ---- links ----

    def _sync_links(self, slot: ShelfSlot) -> None:
        """Unlinked rows are removed (audited unlink); new links are appended in order."""
        rows = self._session.execute(
            select(ShelfSlotDocumentModel.document_id, ShelfSlotDocumentModel.position).where(
                ShelfSlotDocumentModel.slot_id == slot.id.value
            )
        ).all()
        stored = {row.document_id: row.position for row in rows}
        wanted = [document_id.value for document_id in slot.linked_document_ids]
        removed = set(stored) - set(wanted)
        if removed:
            self._session.execute(
                delete(ShelfSlotDocumentModel).where(
                    ShelfSlotDocumentModel.slot_id == slot.id.value,
                    ShelfSlotDocumentModel.document_id.in_(removed),
                )
            )
        added = [
            ComplianceDocumentId(value=value) for value in wanted if value not in stored
        ]
        first_position = max(stored.values(), default=-1) + 1
        self._insert_links(slot, tuple(added), first_position=first_position)

    def _insert_links(
        self,
        slot: ShelfSlot,
        document_ids: Sequence[ComplianceDocumentId],
        *,
        first_position: int,
    ) -> None:
        for offset, document_id in enumerate(document_ids):
            self._session.add(
                ShelfSlotDocumentModel(
                    organization_id=slot.organization_id.value,
                    slot_id=slot.id.value,
                    document_id=document_id.value,
                    position=first_position + offset,
                    linked_at=slot.updated_at,
                    linked_by=slot.updated_by.value,
                )
            )
        if document_ids:
            self._session.flush()

    # ---- loading ----

    def _select(
        self,
        *criteria: ColumnElement[bool],
        organization_id: OrganizationId,
        limit: int | None = None,
    ) -> tuple[ShelfSlot, ...]:
        statement = (
            select(ShelfSlotModel)
            .where(ShelfSlotModel.organization_id == organization_id.value, *criteria)
            .order_by(ShelfSlotModel.code.collate("C"))
        )
        if limit is not None:
            statement = statement.limit(limit)
        models = self._session.scalars(statement).all()
        if not models:
            return ()
        links: dict[UUID, list[ShelfSlotDocumentModel]] = {model.id: [] for model in models}
        for link in self._session.scalars(
            select(ShelfSlotDocumentModel).where(
                ShelfSlotDocumentModel.slot_id.in_(list(links))
            )
        ).all():
            links[link.slot_id].append(link)
        return tuple(slot_to_domain(model, links[model.id]) for model in models)
