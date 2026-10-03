from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentNotFound,
    ComplianceDocumentVersionConflict,
    DuplicateActiveComplianceDocumentCode,
)
from backend.core.domain.repositories.compliance_document_repository import (
    ComplianceDocumentRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_document_query import (
    ComplianceDocumentQuery,
    ComplianceDocumentReviewDueFilter,
)
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentSource,
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork
from backend.core.infrastructure.persistence.in_memory.compliance_document_repository import (
    InMemoryComplianceDocumentRepository,
)
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    advance_to_active,
    compliance_document_draft,
    make_document_type,
    rich_applicability,
    with_file,
)

LATER = FIXED_AT + timedelta(hours=1)


def _archived(document: ComplianceDocument) -> ComplianceDocument:
    return document.archive(
        at=LATER,
        actor_id=document.created_by,
        expected_version=document.version,
        reason="Withdrawn",
    )


class ComplianceDocumentRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> ComplianceDocumentRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_organization_isolation(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document = compliance_document_draft()
        repository.add(document)

        assert repository.get(document.organization_id, document.id) == document
        assert repository.get(OrganizationId(value=uuid4()), document.id) is None
        assert (
            repository.get(
                document.organization_id, ComplianceDocumentId(value=uuid4())
            )
            is None
        )

    def test_rich_round_trip_preserves_state(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document_type = make_document_type(requires_approval_order=True)
        draft = compliance_document_draft(
            document_type,
            issued_at=date(2026, 9, 20),
            next_review_at=date(2031, 9, 30),
            approved_by_document_id=ComplianceDocumentId(value=uuid4()),
            supersedes_document_id=ComplianceDocumentId(value=uuid4()),
            applicability=rich_applicability(),
            source=ComplianceDocumentSource.GENERATED,
            notes="Second edition",
        )
        document = _archived(advance_to_active(with_file(draft), document_type))
        repository.add(document)

        loaded = repository.get(document.organization_id, document.id)
        assert loaded == document
        assert loaded is not None
        assert len(loaded.files) == 2
        assert loaded.current_file == document.files[-1]
        assert loaded.status_before_archive is ComplianceDocumentStatus.ACTIVE

    def test_save_checks_version_and_existence(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document = compliance_document_draft()
        repository.add(document)
        updated = document.update_details(
            at=LATER, actor_id=document.created_by, expected_version=1, title="Renamed"
        )

        repository.save(updated, expected_version=1)
        with pytest.raises(ComplianceDocumentVersionConflict):
            repository.save(updated, expected_version=1)
        reloaded = repository.get(document.organization_id, document.id)
        assert reloaded is not None
        assert reloaded.title == "Renamed"
        assert reloaded.version == 2

        with pytest.raises(ComplianceDocumentNotFound):
            repository.save(compliance_document_draft(), expected_version=1)

    def test_drafts_may_share_a_code(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document_type = make_document_type()
        repository.add(compliance_document_draft(document_type, code="ИОТ-1"))
        repository.add(compliance_document_draft(document_type, code="ИОТ-1"))

    @pytest.mark.parametrize("under_review", [False, True])
    def test_code_is_unique_among_documents_in_force(
        self, repository: ComplianceDocumentRepositoryContract, under_review: bool
    ) -> None:
        document_type = make_document_type()
        in_force = advance_to_active(
            compliance_document_draft(document_type, code="ИОТ-1"), document_type
        )
        if under_review:
            in_force = in_force.start_review(
                at=LATER, actor_id=in_force.created_by, expected_version=in_force.version
            )
        repository.add(in_force)

        with pytest.raises(DuplicateActiveComplianceDocumentCode):
            repository.add(
                advance_to_active(
                    compliance_document_draft(document_type, code="ИОТ-1"),
                    document_type,
                )
            )

        draft = compliance_document_draft(document_type, code="ИОТ-1")
        repository.add(draft)
        with pytest.raises(DuplicateActiveComplianceDocumentCode):
            repository.save(advance_to_active(draft, document_type), expected_version=1)

        foreign_type = make_document_type()
        repository.add(
            advance_to_active(
                compliance_document_draft(foreign_type, code="ИОТ-1"), foreign_type
            )
        )

    def test_superseding_releases_the_code_for_the_new_edition(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document_type = make_document_type()
        old = advance_to_active(
            compliance_document_draft(document_type, code="ИОТ-1"), document_type
        )
        repository.add(old)
        draft = compliance_document_draft(
            document_type, code="ИОТ-1", supersedes_document_id=old.id
        )
        repository.add(draft)
        replacement = advance_to_active(draft, document_type)
        superseded = old.supersede(
            replacement=replacement,
            at=LATER,
            actor_id=old.created_by,
            expected_version=old.version,
        )

        repository.save(superseded, expected_version=old.version)
        repository.save(replacement, expected_version=draft.version)

        reloaded_old = repository.get(old.organization_id, old.id)
        assert reloaded_old is not None
        assert reloaded_old.status is ComplianceDocumentStatus.SUPERSEDED
        assert reloaded_old.superseded_by_document_id == replacement.id

    def test_archived_document_releases_the_code(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document_type = make_document_type()
        active = advance_to_active(
            compliance_document_draft(document_type, code="ИОТ-1"), document_type
        )
        repository.add(active)
        repository.save(_archived(active), expected_version=active.version)

        repository.add(
            advance_to_active(
                compliance_document_draft(document_type, code="ИОТ-1"), document_type
            )
        )

    def test_list_is_scoped_ordered_and_paginated(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        document_type = make_document_type()
        organization_id = document_type.organization_id
        documents = [
            compliance_document_draft(
                document_type,
                code=f"ИОТ-{index}",
                created_at=FIXED_AT + timedelta(minutes=index),
            )
            for index in range(3)
        ]
        for document in (*documents, compliance_document_draft()):
            repository.add(document)

        page = repository.list(
            ComplianceDocumentQuery(organization_id=organization_id, offset=1, limit=1)
        )

        assert page.total == 3
        assert page.items == (documents[1],)
        assert (page.offset, page.limit) == (1, 1)
        everything = repository.list(ComplianceDocumentQuery(organization_id=organization_id))
        assert everything.items == tuple(reversed(documents))

    def test_list_filters(self, repository: ComplianceDocumentRepositoryContract) -> None:
        iot = make_document_type()
        organization_id = iot.organization_id
        order_type = make_document_type(
            organization_id=organization_id, code="order", review_period_months=None
        )
        permit_type = make_document_type(
            organization_id=organization_id,
            code="driver_license",
            subject_kind=DocumentSubjectKind.EMPLOYEE,
            review_period_months=None,
            validity_months=120,
        )
        driver_iot = advance_to_active(
            compliance_document_draft(
                iot, code="ИОТ-001", title="Инструкция для водителя"
            ),
            iot,
        )
        welder_iot = compliance_document_draft(
            iot, code="ИОТ-002", title="Инструкция для сварщика"
        )
        order = compliance_document_draft(order_type, code="ПР-17", title="Приказ о СУОТ")
        permit = compliance_document_draft(
            permit_type, code="ВУ-1", title="Удостоверение", subject_id=uuid4()
        )
        archived = _archived(
            compliance_document_draft(iot, code="ИОТ-OLD", title="Старая инструкция")
        )
        for document in (driver_iot, welder_iot, order, permit, archived):
            repository.add(document)

        def ids(**criteria) -> set[ComplianceDocumentId]:
            page = repository.list(
                ComplianceDocumentQuery(organization_id=organization_id, **criteria)
            )
            assert page.total == len(page.items)
            return {item.id for item in page.items}

        assert ids() == {driver_iot.id, welder_iot.id, order.id, permit.id}
        assert ids(include_archived=True) == {
            driver_iot.id,
            welder_iot.id,
            order.id,
            permit.id,
            archived.id,
        }
        assert ids(document_type_ids=frozenset({iot.id})) == {driver_iot.id, welder_iot.id}
        assert ids(document_type_ids=frozenset()) == set()
        assert ids(status=ComplianceDocumentStatus.ACTIVE) == {driver_iot.id}
        assert ids(subject_kind=DocumentSubjectKind.EMPLOYEE) == {permit.id}
        assert ids(search="  сварщ ") == {welder_iot.id}
        assert ids(search="пр-17") == {order.id}
        assert ids(search="СТАРАЯ", include_archived=True) == {archived.id}

    def test_list_review_due_filter_uses_document_types(
        self, repository: ComplianceDocumentRepositoryContract
    ) -> None:
        as_of = date(2026, 10, 1)
        iot = make_document_type(warning_thresholds_days=(30,))
        organization_id = iot.organization_id
        unreviewed_type = make_document_type(
            organization_id=organization_id, code="order", review_period_months=None
        )

        def active(document_type, code: str, next_review_at: date) -> ComplianceDocument:
            return advance_to_active(
                compliance_document_draft(
                    document_type, code=code, next_review_at=next_review_at
                ),
                document_type,
            )

        due = active(iot, "ИОТ-1", as_of + timedelta(days=30))
        not_due = active(iot, "ИОТ-2", as_of + timedelta(days=31))
        no_period = active(unreviewed_type, "ПР-1", as_of)
        draft = compliance_document_draft(iot, code="ИОТ-3", next_review_at=as_of)
        for document in (due, not_due, no_period, draft):
            repository.add(document)

        page = repository.list(
            ComplianceDocumentQuery(
                organization_id=organization_id,
                review_due=ComplianceDocumentReviewDueFilter(
                    as_of=as_of,
                    document_types={
                        iot.id: iot,
                        unreviewed_type.id: unreviewed_type,
                    },
                ),
            )
        )

        assert page.items == (due,)
        assert page.total == 1


class TestInMemoryComplianceDocumentRepository(ComplianceDocumentRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> ComplianceDocumentRepositoryContract:
        return InMemoryComplianceDocumentRepository()


def test_in_memory_unit_of_work_commits_compliance_repositories() -> None:
    unit_of_work = InMemoryUnitOfWork()
    document_type = make_document_type()
    document = compliance_document_draft(document_type)

    with unit_of_work:
        unit_of_work.document_types.add(document_type)
        unit_of_work.compliance_documents.add(document)
        unit_of_work.commit()

    with unit_of_work:
        assert (
            unit_of_work.document_types.get(document_type.organization_id, document_type.id)
            == document_type
        )
        assert (
            unit_of_work.compliance_documents.get(document.organization_id, document.id)
            == document
        )


def test_in_memory_unit_of_work_rolls_back_compliance_repositories() -> None:
    unit_of_work = InMemoryUnitOfWork()
    document_type = make_document_type()
    document = compliance_document_draft(document_type)

    with pytest.raises(RuntimeError), unit_of_work:
        unit_of_work.document_types.add(document_type)
        unit_of_work.compliance_documents.add(document)
        raise RuntimeError("rollback")

    assert (
        unit_of_work.document_types.get(document_type.organization_id, document_type.id)
        is None
    )
    assert unit_of_work.compliance_documents.get(document.organization_id, document.id) is None
