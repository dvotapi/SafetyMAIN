from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
from backend.core.domain.value_objects.shelf_enums import SlotExclusionReason
from backend.core.infrastructure.persistence.sqlalchemy.mappers.shelf_mapper import (
    slot_columns,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.shelf_model import (
    ShelfSlotDocumentModel,
    ShelfSlotModel,
    ShelfSubsectionModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.shelf_section_repository import (
    SQLAlchemyShelfSectionRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.shelf_slot_repository import (
    SQLAlchemyShelfSlotRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_sqlalchemy_shelf_contracts import ensure_shelf_slot_related
from tests.fixtures.compliance_documents import FIXED_AT, make_actor
from tests.fixtures.shelf import make_section, make_slot

pytest_plugins = ("tests.infrastructure.db_fixtures",)


def _stored_slot(session: Session) -> ShelfSlot:
    section = make_section()
    ensure_organization(session, section.organization_id)
    SQLAlchemyShelfSectionRepository(session).add(section)
    slot = make_slot(section)
    ensure_shelf_slot_related(session, slot)
    SQLAlchemyShelfSlotRepository(session).add(slot)
    session.flush()
    return slot


def _violates(session: Session, constraint: str, change: Callable[[], Any]) -> None:
    savepoint = session.begin_nested()
    with pytest.raises(IntegrityError, match=constraint):
        change()
        session.flush()
    savepoint.rollback()


def _set(session: Session, slot: ShelfSlot, **values: Any) -> Callable[[], Any]:
    return lambda: session.execute(
        update(ShelfSlotModel).where(ShelfSlotModel.id == slot.id.value).values(**values)
    )


@pytest.mark.db
def test_slot_constraints(sqlalchemy_session: Session) -> None:
    session = sqlalchemy_session
    slot = _stored_slot(session)
    actor = make_actor()
    ensure_user(session, actor)

    _violates(
        session,
        "ck_shelf_slots_exclusion_complete",
        _set(session, slot, exclusion_reason="other", exclusion_comment="Причина"),
    )
    _violates(
        session,
        "ck_shelf_slots_exclusion_comment_length",
        _set(
            session,
            slot,
            exclusion_reason="other",
            exclusion_comment="  ab  ",
            exclusion_status_before="missing",
            excluded_by=actor.value,
            excluded_at=FIXED_AT,
        ),
    )
    _violates(
        session,
        "ck_shelf_slots_condition_required",
        _set(session, slot, obligation_level="conditional", applicability_condition=""),
    )
    _violates(session, "ck_shelf_slots_curated_status", _set(session, slot, curated_status="x"))
    _violates(session, "ck_shelf_slots_kept_on", _set(session, slot, kept_on="vehicle"))
    _violates(session, "ck_shelf_slots_title_length", _set(session, slot, title=""))
    _violates(session, "ck_shelf_slots_version_positive", _set(session, slot, version=0))
    _violates(
        session,
        "uq_shelf_slots_organization_id_code",
        lambda: session.add(ShelfSlotModel(**{**slot_columns(slot), "id": uuid4()})),
    )


@pytest.mark.db
def test_link_and_subsection_constraints(sqlalchemy_session: Session) -> None:
    session = sqlalchemy_session
    slot = _stored_slot(session)

    _violates(
        session,
        "shelf_slot_documents_document_id_fkey",
        lambda: session.add(
            ShelfSlotDocumentModel(
                organization_id=slot.organization_id.value,
                slot_id=slot.id.value,
                document_id=ComplianceDocumentId(value=uuid4()).value,
                position=0,
                linked_at=FIXED_AT,
                linked_by=slot.created_by.value,
            )
        ),
    )
    _violates(
        session,
        "uq_shelf_subsections_section_id_position",
        lambda: session.add(
            ShelfSubsectionModel(
                id=uuid4(),
                organization_id=slot.organization_id.value,
                section_id=slot.section_id.value,
                code="ТрБ.09",
                title="Дубль позиции",
                position=0,
            )
        ),
    )


@pytest.mark.db
def test_shelf_survives_commit_and_new_unit_of_work(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    section = make_section()
    slot = make_slot(section)
    actor = make_actor()
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        ensure_organization(uow.session, section.organization_id)
        for user_id in (slot.created_by, actor):
            ensure_user(uow.session, user_id)
        uow.shelf_sections.add(section)
        uow.shelf_slots.add(slot)
        uow.commit()

    excluded = slot.exclude(
        reason=SlotExclusionReason.NOT_APPLICABLE,
        comment="Не применимо к нам",
        at=FIXED_AT + timedelta(hours=1),
        actor_id=actor,
        expected_version=1,
    )
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        uow.shelf_slots.save(excluded, expected_version=1)
        uow.commit()

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        assert uow.shelf_sections.get(section.organization_id, section.id) == section
        assert uow.shelf_slots.get(slot.organization_id, slot.id) == excluded


@pytest.mark.db
def test_unit_of_work_rolls_back_shelf_changes(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    section = make_section()
    with pytest.raises(RuntimeError), SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        ensure_organization(uow.session, section.organization_id)
        uow.shelf_sections.add(section)
        raise RuntimeError("boom")

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        assert uow.shelf_sections.get(section.organization_id, section.id) is None
