"""Shelf handlers against PostgreSQL: one unit of work per command, as over HTTP."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
)
from backend.core.application.commands.shelf import (
    BulkExcludeShelfSlotsCommand,
    CreateShelfSectionCommand,
    CreateShelfSlotCommand,
    DevelopShelfSlotDocumentCommand,
)
from backend.core.application.handlers.shelf import (
    BulkExcludeShelfSlotsHandler,
    CreateShelfSectionHandler,
    CreateShelfSlotHandler,
    DevelopShelfSlotDocumentHandler,
    GetShelfOverviewHandler,
)
from backend.core.application.queries.shelf import GetShelfOverviewQuery
from backend.core.domain.exceptions.shelf import ShelfSlotsVersionConflict
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    ShelfStatusGroup,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model import (
    AuditEventModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.fixtures.compliance_documents import FIXED_AT, make_document_type

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class FixedClock:
    def now(self) -> datetime:
        return FIXED_AT


@pytest.mark.db
def test_shelf_commands_persist_atomically_with_their_audit_events(
    sqlalchemy_session_factory: sessionmaker,
) -> None:
    organization_id = OrganizationId(value=uuid4())
    actor = UserId(value=uuid4())
    context = AuditContext(actor_user_id=actor, authorization_organization_id=organization_id)
    clock = FixedClock()

    def uow() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(sqlalchemy_session_factory)

    audit = AdministrativeAuditRecorder(clock, uow)

    def run[T](build: Callable[[SQLAlchemyUnitOfWork], T]) -> T:
        with uow() as unit_of_work:
            return build(unit_of_work)

    with uow() as seed:
        ensure_organization(seed.session, organization_id)
        ensure_user(seed.session, actor)
        seed.document_types.add(make_document_type(organization_id=organization_id, code="plan"))
        seed.commit()

    section = run(
        lambda unit_of_work: CreateShelfSectionHandler(unit_of_work, clock, audit).handle(
            CreateShelfSectionCommand(
                organization_id=organization_id,
                actor_id=actor,
                code="ТрБ",
                number=10,
                title="Транспортная безопасность",
                safety_domain=SafetyDomain.TRANSPORT_SECURITY,
                subsections=(("ТрБ.01", "Оценка"), ("ТрБ.02", "План")),
                audit_context=context,
            )
        )
    )
    created = [
        run(
            lambda unit_of_work, code=code: CreateShelfSlotHandler(
                unit_of_work, clock, audit
            ).handle(
                CreateShelfSlotCommand(
                    organization_id=organization_id,
                    actor_id=actor,
                    code=code,
                    title=f"Место {code}",
                    short_title=code,
                    document_kind="План",
                    kept_on=SlotKeptOn.ORGANIZATION,
                    obligation_level=SlotObligationLevel.MANDATORY,
                    curated_status=CuratedSlotStatus.MISSING,
                    document_type_code="plan",
                    audit_context=context,
                )
            )
        )
        for code in ("ТрБ.01.01", "ТрБ.01.02", "ТрБ.02.01")
    ]
    assert section.code == "ТрБ"

    developed = run(
        lambda unit_of_work: DevelopShelfSlotDocumentHandler(unit_of_work, clock, audit).handle(
            DevelopShelfSlotDocumentCommand(
                organization_id=organization_id,
                slot_id=created[0].slot.id,
                actor_id=actor,
                expected_version=1,
                audit_context=context,
            )
        )
    )

    with pytest.raises(ShelfSlotsVersionConflict):
        run(
            lambda unit_of_work: BulkExcludeShelfSlotsHandler(unit_of_work, clock, audit).handle(
                BulkExcludeShelfSlotsCommand(
                    organization_id=organization_id,
                    actor_id=actor,
                    items=((created[1].slot.id, 1), (created[2].slot.id, 9)),
                    reason=SlotExclusionReason.OTHER,
                    comment="Не требуется",
                    audit_context=context,
                )
            )
        )
    run(
        lambda unit_of_work: BulkExcludeShelfSlotsHandler(unit_of_work, clock, audit).handle(
            BulkExcludeShelfSlotsCommand(
                organization_id=organization_id,
                actor_id=actor,
                items=((created[1].slot.id, 1), (created[2].slot.id, 1)),
                reason=SlotExclusionReason.OTHER,
                comment="Не требуется",
                audit_context=context,
            )
        )
    )

    overview = run(
        lambda unit_of_work: GetShelfOverviewHandler(unit_of_work, clock).handle(
            GetShelfOverviewQuery(organization_id=organization_id)
        )
    )
    assert overview.totals.total == 3
    assert overview.totals.by_group[ShelfStatusGroup.IN_PROGRESS] == 1
    assert overview.totals.by_group[ShelfStatusGroup.EXCLUDED] == 2
    assert overview.totals.readiness_percent == 67

    with uow() as check:
        document = check.compliance_documents.get(organization_id, developed.document.id)
        assert document is not None and document.code == "ТрБ.01.01"
        slot = check.shelf_slots.get(organization_id, created[0].slot.id)
        assert slot is not None and slot.linked_document_ids == (document.id,)
        actions = check.session.execute(
            select(AuditEventModel.action, AuditEventModel.outcome, func.count())
            .where(AuditEventModel.target_organization_id == organization_id.value)
            .group_by(AuditEventModel.action, AuditEventModel.outcome)
        ).all()
    assert {(row[0], row[1]): row[2] for row in actions} == {
        ("compliance.section.created", "SUCCESS"): 1,
        ("compliance.place.created", "SUCCESS"): 3,
        ("compliance.document.created", "SUCCESS"): 1,
        ("compliance.place.linked", "SUCCESS"): 1,
        ("compliance.place.excluded", "FAILURE"): 1,
        ("compliance.place.excluded", "SUCCESS"): 2,
    }
