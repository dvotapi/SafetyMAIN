from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.exceptions.shelf import (
    ShelfSlotAlreadyExcluded,
    ShelfSlotCodeMismatch,
    ShelfSlotDocumentAlreadyLinked,
    ShelfSlotDocumentNotFound,
    ShelfSlotDocumentNotLinked,
    ShelfSlotDocumentSubjectNotSupported,
    ShelfSlotExclusionCommentTooShort,
    ShelfSlotNotExcluded,
    ShelfSlotNotToClarify,
    ShelfSlotValidationError,
    ShelfSlotVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)
from backend.core.domain.value_objects.shelf_values import SlotLegalBasis
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    compliance_document_draft,
    make_actor,
    make_document_type,
)
from tests.fixtures.shelf import make_section, make_slot

LATER = FIXED_AT + timedelta(hours=1)


def _document(slot_org: OrganizationId, status: ComplianceDocumentStatus) -> ComplianceDocument:
    document = compliance_document_draft(make_document_type(organization_id=slot_org))
    return document.model_copy(update={"status": status})


def test_create_derives_section_and_subsection_from_code() -> None:
    section = make_section()
    slot = make_slot(section, code="ТрБ.02.03")
    assert slot.code.value == "ТрБ.02.03"
    assert slot.section_id == section.id
    assert slot.subsection_id == section.subsections[1].id
    assert slot.version == 1
    assert slot.linked_document_ids == ()
    assert slot.exclusion is None


@pytest.mark.parametrize("code", ["ВМ.01.01", "ТрБ.03.01", "ТрБ.01.1"])
def test_create_rejects_code_outside_section_subsections(code: str) -> None:
    with pytest.raises((ShelfSlotCodeMismatch, ShelfSlotValidationError)):
        make_slot(make_section(), code=code)


def test_create_rejects_section_of_another_organization() -> None:
    section = make_section()
    with pytest.raises(ShelfSlotCodeMismatch):
        ShelfSlot.create(
            organization_id=OrganizationId(value=uuid4()),
            section=section,
            code="ТрБ.01.02",
            title="T",
            short_title="T",
            document_kind="План",
            kept_on=SlotKeptOn.ORGANIZATION,
            obligation_level=SlotObligationLevel.MANDATORY,
            curated_status=CuratedSlotStatus.MISSING,
            created_by=make_actor(),
            created_at=FIXED_AT,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": " "},
        {"title": "x" * 501},
        {"short_title": "x" * 41},
        {"short_title": ""},
        {"document_kind": "Памятка"},
        {"review_period_months": 0},
    ],
)
def test_field_rules(overrides: dict[str, Any]) -> None:
    with pytest.raises(ShelfSlotValidationError):
        make_slot(**overrides)


def test_conditional_place_requires_condition() -> None:
    with pytest.raises(ShelfSlotValidationError):
        make_slot(
            obligation_level=SlotObligationLevel.CONDITIONAL, applicability_condition=" "
        )
    slot = make_slot(obligation_level=SlotObligationLevel.CONDITIONAL)
    assert slot.applicability_condition == "При наличии ОТИ"


def test_update_details_changes_curated_fields_only() -> None:
    slot = make_slot()
    actor = make_actor()
    updated = slot.update_details(
        at=LATER,
        actor_id=actor,
        expected_version=1,
        short_title="ПОТБ",
        legal_basis=SlotLegalBasis(regulation="16-ФЗ", clause="ст. 8"),
        review_period_months=None,
        document_type_code="  ",
    )
    assert updated.short_title == "ПОТБ"
    assert updated.legal_basis.regulation == "16-ФЗ"
    assert updated.document_type_code is None
    assert (updated.version, updated.updated_by, updated.updated_at) == (2, actor, LATER)
    with pytest.raises(ShelfSlotValidationError):
        updated.update_details(at=LATER, actor_id=actor, expected_version=2, code="ТрБ.01.09")


def test_update_without_changes_returns_same_place() -> None:
    slot = make_slot()
    assert slot.update_details(at=LATER, actor_id=make_actor(), expected_version=1, title=slot.title) is slot


def test_exclude_and_restore() -> None:
    slot = make_slot(curated_status=CuratedSlotStatus.IN_PROGRESS)
    actor = make_actor()
    excluded = slot.exclude(
        reason=SlotExclusionReason.NOT_APPLICABLE,
        comment="  Нет ОТИ  ",
        at=LATER,
        actor_id=actor,
        expected_version=1,
    )
    assert excluded.is_excluded
    assert excluded.exclusion is not None
    assert excluded.exclusion.comment == "Нет ОТИ"
    assert excluded.exclusion.status_before is CuratedSlotStatus.IN_PROGRESS
    assert (excluded.exclusion.excluded_by, excluded.exclusion.excluded_at) == (actor, LATER)
    with pytest.raises(ShelfSlotAlreadyExcluded):
        excluded.exclude(
            reason=SlotExclusionReason.OTHER,
            comment="Повторно",
            at=LATER,
            actor_id=actor,
            expected_version=2,
        )
    restored = excluded.restore(at=LATER, actor_id=actor, expected_version=2)
    assert restored.exclusion is None
    assert restored.curated_status is CuratedSlotStatus.IN_PROGRESS
    with pytest.raises(ShelfSlotNotExcluded):
        restored.restore(at=LATER, actor_id=actor, expected_version=3)


@pytest.mark.parametrize("comment", ["", "    ", "abcd", "  ab  "])
def test_exclusion_comment_needs_five_characters_after_trim(comment: str) -> None:
    with pytest.raises(ShelfSlotExclusionCommentTooShort):
        make_slot().exclude(
            reason=SlotExclusionReason.OTHER,
            comment=comment,
            at=LATER,
            actor_id=make_actor(),
            expected_version=1,
        )


def test_exclusion_comment_at_most_1000_characters() -> None:
    with pytest.raises(ShelfSlotValidationError):
        make_slot().exclude(
            reason=SlotExclusionReason.OTHER,
            comment="x" * 1001,
            at=LATER,
            actor_id=make_actor(),
            expected_version=1,
        )


def test_excluded_place_blocks_commands_but_allows_detail_edits() -> None:
    slot = make_slot(curated_status=CuratedSlotStatus.TO_CLARIFY).exclude(
        reason=SlotExclusionReason.CONDITION_NOT_MET,
        comment="Нет такого объекта",
        at=LATER,
        actor_id=make_actor(),
        expected_version=1,
    )
    actor = make_actor()
    document = _document(slot.organization_id, ComplianceDocumentStatus.DRAFT)
    with pytest.raises(ShelfSlotAlreadyExcluded):
        slot.confirm_applicable(at=LATER, actor_id=actor, expected_version=2)
    with pytest.raises(ShelfSlotAlreadyExcluded):
        slot.link_document(
            document=document, linked_documents=(), at=LATER, actor_id=actor, expected_version=2
        )
    with pytest.raises(ShelfSlotAlreadyExcluded):
        slot.ensure_can_develop(())
    with pytest.raises(ShelfSlotAlreadyExcluded):
        slot.update_details(
            at=LATER,
            actor_id=actor,
            expected_version=2,
            curated_status=CuratedSlotStatus.MISSING,
        )
    edited = slot.update_details(at=LATER, actor_id=actor, expected_version=2, notes="Заметка")
    assert edited.notes == "Заметка"


def test_confirm_applicable_only_from_to_clarify() -> None:
    slot = make_slot(curated_status=CuratedSlotStatus.TO_CLARIFY)
    confirmed = slot.confirm_applicable(at=LATER, actor_id=make_actor(), expected_version=1)
    assert confirmed.curated_status is CuratedSlotStatus.MISSING
    with pytest.raises(ShelfSlotNotToClarify):
        confirmed.confirm_applicable(at=LATER, actor_id=make_actor(), expected_version=2)


def test_link_is_idempotent_and_unlink_removes() -> None:
    slot = make_slot()
    actor = make_actor()
    document = _document(slot.organization_id, ComplianceDocumentStatus.ACTIVE)
    linked = slot.link_document(
        document=document, linked_documents=(), at=LATER, actor_id=actor, expected_version=1
    )
    assert linked.linked_document_ids == (document.id,)
    again = linked.link_document(
        document=document,
        linked_documents=(document,),
        at=LATER,
        actor_id=actor,
        expected_version=2,
    )
    assert again is linked
    unlinked = linked.unlink_document(
        document_id=document.id, at=LATER, actor_id=actor, expected_version=2
    )
    assert unlinked.linked_document_ids == ()
    with pytest.raises(ShelfSlotDocumentNotLinked):
        unlinked.unlink_document(
            document_id=document.id, at=LATER, actor_id=actor, expected_version=3
        )


def test_link_rejects_foreign_and_non_organization_documents() -> None:
    slot = make_slot()
    actor = make_actor()
    foreign = _document(OrganizationId(value=uuid4()), ComplianceDocumentStatus.ACTIVE)
    with pytest.raises(ShelfSlotDocumentNotFound):
        slot.link_document(
            document=foreign, linked_documents=(), at=LATER, actor_id=actor, expected_version=1
        )
    employee_doc = _document(slot.organization_id, ComplianceDocumentStatus.ACTIVE).model_copy(
        update={"subject_kind": DocumentSubjectKind.EMPLOYEE}
    )
    with pytest.raises(ShelfSlotDocumentSubjectNotSupported):
        slot.link_document(
            document=employee_doc,
            linked_documents=(),
            at=LATER,
            actor_id=actor,
            expected_version=1,
        )


def test_only_one_linked_document_in_force() -> None:
    slot = make_slot()
    actor = make_actor()
    current = _document(slot.organization_id, ComplianceDocumentStatus.ACTIVE)
    slot = slot.link_document(
        document=current, linked_documents=(), at=LATER, actor_id=actor, expected_version=1
    )
    second = _document(slot.organization_id, ComplianceDocumentStatus.UNDER_REVIEW)
    with pytest.raises(ShelfSlotDocumentAlreadyLinked):
        slot.link_document(
            document=second,
            linked_documents=(current,),
            at=LATER,
            actor_id=actor,
            expected_version=2,
        )
    previous = _document(slot.organization_id, ComplianceDocumentStatus.SUPERSEDED)
    slot = slot.link_document(
        document=previous,
        linked_documents=(current,),
        at=LATER,
        actor_id=actor,
        expected_version=2,
    )
    assert slot.linked_document_ids == (current.id, previous.id)


@pytest.mark.parametrize(
    ("status", "allowed"),
    [
        (ComplianceDocumentStatus.DRAFT, False),
        (ComplianceDocumentStatus.APPROVED, False),
        (ComplianceDocumentStatus.ACTIVE, False),
        (ComplianceDocumentStatus.UNDER_REVIEW, False),
        (ComplianceDocumentStatus.SUPERSEDED, True),
        (ComplianceDocumentStatus.ARCHIVED, True),
    ],
)
def test_develop_needs_no_document_in_progress_or_in_force(
    status: ComplianceDocumentStatus, allowed: bool
) -> None:
    slot = make_slot()
    document = _document(slot.organization_id, status)
    slot = slot.model_copy(update={"linked_document_ids": (document.id,)})
    if allowed:
        slot.ensure_can_develop((document,))
    else:
        with pytest.raises(ShelfSlotDocumentAlreadyLinked):
            slot.ensure_can_develop((document,))


def test_commands_check_version() -> None:
    slot = make_slot(curated_status=CuratedSlotStatus.TO_CLARIFY)
    actor = make_actor()
    with pytest.raises(ShelfSlotVersionConflict):
        slot.confirm_applicable(at=LATER, actor_id=actor, expected_version=2)
    with pytest.raises(ShelfSlotVersionConflict):
        slot.exclude(
            reason=SlotExclusionReason.OTHER,
            comment="Причина",
            at=LATER,
            actor_id=actor,
            expected_version=0,
        )
    with pytest.raises(ShelfSlotVersionConflict):
        slot.update_details(at=LATER, actor_id=actor, expected_version=3, notes="x")


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "ftp://example.org/doc",
        "//example.org/doc",
        "example.org/doc",
        "https://" + "a" * 2048,
    ],
)
def test_legal_basis_rejects_unsafe_source_urls(url: str) -> None:
    from backend.core.domain.value_objects.shelf_values import SlotLegalBasis

    with pytest.raises(ValueError):
        SlotLegalBasis(source_url=url)


def test_legal_basis_keeps_http_urls_and_clears_blank_ones() -> None:
    from backend.core.domain.value_objects.shelf_values import SlotLegalBasis

    assert SlotLegalBasis(source_url=" https://pravo.gov.ru/doc ").source_url == (
        "https://pravo.gov.ru/doc"
    )
    assert SlotLegalBasis(source_url="  ").source_url is None
