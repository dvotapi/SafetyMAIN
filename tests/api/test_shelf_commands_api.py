"""Shelf curator commands: preconditions (422), concurrency (409), tenancy (404), audit."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import DocumentSubjectKind
from backend.core.domain.value_objects.shelf_enums import CuratedSlotStatus
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.shelf_support import ShelfClient, build_shelf_client
from tests.fixtures.compliance_documents import (
    advance_to_active,
    compliance_document_draft,
    make_document_type,
)
from tests.fixtures.shelf import make_section, make_slot

COMMENT = "Нет объектов на балансе"


@pytest.fixture
def shelf() -> ShelfClient:
    return build_shelf_client()


def _exclude(shelf: ShelfClient, slot_id: object, version: int = 1, **overrides: Any) -> Any:
    body = {"reason": "not_applicable", "comment": COMMENT, "version": version, **overrides}
    return shelf.post(f"/slots/{slot_id}/exclude", body)


def _create_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "code": "ТрБ.01.05",
        "title": "Паспорт обеспечения транспортной безопасности",
        "short_title": "Паспорт ОТБ",
        "document_kind": "Проект / паспорт",
        "kept_on": "facility",
        "obligation_level": "mandatory",
        **overrides,
    }


# ---- create / update ----


def test_create_slot_returns_detail_and_audits(shelf: ShelfClient) -> None:
    shelf.seed_section()

    response = shelf.post(
        "/slots",
        _create_payload(
            document_type_code="transport_plan",
            legal_basis={"regulation": "16-ФЗ", "clause": "ст. 8", "confidence": "verified"},
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert response.headers["Location"].endswith(f"/shelf/slots/{body['id']}")
    assert body["effective_status"] == "missing"
    assert body["primary_action"] == "develop_document"
    assert body["legal_basis"]["confidence"] == "verified"
    (event,) = shelf.events("compliance.place.created")
    assert event.metadata["slot_code"] == "ТрБ.01.05"
    assert event.metadata["section_code"] == "ТрБ"
    assert event.resource_type.value == "SHELF_PLACE"


@pytest.mark.parametrize(
    ("overrides", "status", "code"),
    [
        ({"code": "ПожБ.01.01"}, 422, "shelf_slot_code_mismatch"),
        ({"code": "ТрБ.07.01"}, 422, "shelf_slot_code_mismatch"),
        ({"code": "TRB.01.01"}, 422, "shelf_slot_validation_error"),
        ({"document_kind": "Письмо"}, 422, "shelf_slot_validation_error"),
        ({"short_title": "x" * 41}, 422, "shelf_slot_validation_error"),
        ({"obligation_level": "conditional"}, 422, "shelf_slot_validation_error"),
        ({"document_type_code": "unknown_type"}, 422, "document_type_not_found"),
    ],
)
def test_create_slot_rejections(
    shelf: ShelfClient, overrides: dict[str, Any], status: int, code: str
) -> None:
    shelf.seed_section()

    assert_error_envelope(
        shelf.post("/slots", _create_payload(**overrides)), status_code=status, code=code
    )


def test_duplicate_code_is_409_even_when_the_existing_place_is_excluded(
    shelf: ShelfClient,
) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, code="ТрБ.01.05")
    assert _exclude(shelf, slot.id.value).status_code == 200

    assert_error_envelope(
        shelf.post("/slots", _create_payload()),
        status_code=409,
        code="duplicate_shelf_slot_code",
    )
    failures = [e for e in shelf.events("compliance.place.created") if e.failure_code]
    assert failures and failures[-1].failure_code == "duplicate_shelf_slot_code"


def test_update_changes_only_sent_fields_and_audits_them(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, review_period_months=36)

    response = shelf.patch(
        f"/slots/{slot.id.value}",
        {"version": 1, "short_title": "План ОТБ (ред.)", "review_period_months": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["short_title"] == "План ОТБ (ред.)"
    assert body["review_period_months"] is None
    assert body["title"] == slot.title
    assert body["version"] == 2
    (event,) = shelf.events("compliance.place.updated")
    assert event.metadata["changed_fields"] == "review_period_months,short_title"
    assert_error_envelope(
        shelf.patch(f"/slots/{slot.id.value}", {"version": 1, "notes": "stale"}),
        status_code=409,
        code="shelf_slot_version_conflict",
    )


def test_update_rejects_an_unknown_field(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)

    response = shelf.patch(f"/slots/{slot.id.value}", {"version": 1, "code": "ТрБ.01.09"})

    assert response.status_code == 422


# ---- exclude / restore / confirm ----


def test_exclude_and_restore_round_trip(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, curated_status=CuratedSlotStatus.TO_CLARIFY)

    excluded = _exclude(shelf, slot.id.value, reason="condition_not_met")
    assert excluded.status_code == 200
    assert excluded.json()["effective_status"] == "excluded"
    assert excluded.json()["exclusion"]["comment"] == COMMENT

    restored = shelf.post(f"/slots/{slot.id.value}/restore", {"version": 2})
    assert restored.status_code == 200
    assert restored.json()["effective_status"] == "to_clarify"
    assert restored.json()["exclusion"] is None

    (exclude_event,) = shelf.events("compliance.place.excluded")
    assert exclude_event.metadata["reason"] == "condition_not_met"
    assert exclude_event.metadata["comment"] == COMMENT
    assert exclude_event.metadata["expected_version"] == "1"
    assert exclude_event.metadata["resulting_version"] == "2"
    (restore_event,) = shelf.events("compliance.place.restored")
    assert restore_event.metadata["new_status"] == "to_clarify"


def test_exclude_preconditions(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)

    assert_error_envelope(
        _exclude(shelf, slot.id.value, comment="  abc "),
        status_code=422,
        code="comment_too_short",
    )
    assert_error_envelope(
        _exclude(shelf, slot.id.value, version=7),
        status_code=409,
        code="shelf_slot_version_conflict",
    )
    assert _exclude(shelf, slot.id.value).status_code == 200
    assert_error_envelope(
        _exclude(shelf, slot.id.value, version=2), status_code=422, code="already_excluded"
    )
    assert_error_envelope(
        shelf.post(f"/slots/{slot.id.value}/confirm-applicable", {"version": 2}),
        status_code=422,
        code="already_excluded",
    )


def test_restore_requires_an_excluded_place(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)

    assert_error_envelope(
        shelf.post(f"/slots/{slot.id.value}/restore", {"version": 1}),
        status_code=422,
        code="not_excluded",
    )
    failures = [e for e in shelf.events("compliance.place.restored") if e.failure_code]
    assert failures[-1].failure_code == "not_excluded"


def test_confirm_applicable(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    to_clarify = shelf.seed_slot(section, curated_status=CuratedSlotStatus.TO_CLARIFY)
    missing = shelf.seed_slot(section, code="ТрБ.01.02")

    confirmed = shelf.post(f"/slots/{to_clarify.id.value}/confirm-applicable", {"version": 1})
    assert confirmed.status_code == 200
    assert confirmed.json()["effective_status"] == "missing"
    assert confirmed.json()["curated_status"] == "missing"
    (event,) = shelf.events("compliance.place.confirmed")
    assert event.metadata["previous_status"] == "to_clarify"

    assert_error_envelope(
        shelf.post(f"/slots/{missing.id.value}/confirm-applicable", {"version": 1}),
        status_code=422,
        code="not_to_clarify",
    )


# ---- bulk exclude ----


def test_bulk_exclude_is_all_or_nothing(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    first = shelf.seed_slot(section, code="ТрБ.01.01")
    second = shelf.seed_slot(section, code="ТрБ.01.02")
    third = shelf.seed_slot(section, code="ТрБ.01.03")
    assert _exclude(shelf, third.id.value).status_code == 200

    def bulk(items: list[tuple[object, int]]) -> Any:
        return shelf.post(
            "/slots/bulk-exclude",
            {
                "items": [{"slot_id": str(i), "version": v} for i, v in items],
                "reason": "duplicate",
                "comment": COMMENT,
            },
        )

    conflict = bulk([(first.id.value, 1), (second.id.value, 5)])
    assert_error_envelope(conflict, status_code=409, code="shelf_slot_version_conflict")
    assert conflict.json()["error"]["details"]["conflicting_slot_ids"] == [
        str(second.id.value)
    ]

    already = bulk([(first.id.value, 1), (third.id.value, 2)])
    assert_error_envelope(already, status_code=422, code="already_excluded")
    assert already.json()["error"]["details"]["excluded_slot_ids"] == [str(third.id.value)]

    foreign = bulk([(first.id.value, 1), (uuid4(), 1)])
    assert_error_envelope(foreign, status_code=404, code="shelf_slot_not_found")

    stored = shelf.slots.get(shelf.organization_id, first.id)
    assert stored is not None and stored.version == 1 and not stored.is_excluded

    done = bulk([(first.id.value, 1), (second.id.value, 1)])
    assert done.status_code == 200
    assert [item["effective_status"] for item in done.json()["items"]] == [
        "excluded",
        "excluded",
    ]
    successes = [e for e in shelf.events("compliance.place.excluded") if not e.failure_code]
    assert {e.metadata["slot_code"] for e in successes} == {
        "ТрБ.01.01",
        "ТрБ.01.02",
        "ТрБ.01.03",
    }


@pytest.mark.parametrize("count", [0, 201])
def test_bulk_exclude_size_limits(shelf: ShelfClient, count: int) -> None:
    response = shelf.post(
        "/slots/bulk-exclude",
        {
            "items": [{"slot_id": str(uuid4()), "version": 1} for _ in range(count)],
            "reason": "other",
            "comment": COMMENT,
        },
    )

    assert response.status_code == 422


def test_bulk_exclude_rejects_repeated_places(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)
    item = {"slot_id": str(slot.id.value), "version": 1}

    response = shelf.post(
        "/slots/bulk-exclude", {"items": [item, item], "reason": "other", "comment": COMMENT}
    )

    assert_error_envelope(response, status_code=422, code="shelf_slot_validation_error")


# ---- link / unlink ----


def test_link_and_unlink_documents(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)
    draft = compliance_document_draft(shelf.document_type, code="ПОТБ-1")
    shelf.documents.add(draft)

    linked = shelf.post(
        f"/slots/{slot.id.value}/documents",
        {"document_id": str(draft.id.value), "version": 1},
    )
    assert linked.status_code == 200
    assert linked.json()["effective_status"] == "in_progress"
    assert linked.json()["primary_action"] == "open_project"
    (event,) = shelf.events("compliance.place.linked")
    assert event.metadata["document_code"] == "ПОТБ-1"

    again = shelf.post(
        f"/slots/{slot.id.value}/documents",
        {"document_id": str(draft.id.value), "version": 2},
    )
    assert again.status_code == 200
    assert again.json()["version"] == 2
    assert len(shelf.events("compliance.place.linked")) == 1

    unlinked = shelf.post(
        f"/slots/{slot.id.value}/documents/{draft.id.value}/unlink", {"version": 2}
    )
    assert unlinked.status_code == 200
    assert unlinked.json()["effective_status"] == "missing"
    assert unlinked.json()["editions"] == []
    assert shelf.documents.get(shelf.organization_id, draft.id) is not None
    (unlink_event,) = shelf.events("compliance.place.unlinked")
    assert unlink_event.metadata["document_id"] == str(draft.id.value)

    assert_error_envelope(
        shelf.post(f"/slots/{slot.id.value}/documents/{draft.id.value}/unlink", {"version": 3}),
        status_code=404,
        code="shelf_slot_document_not_linked",
    )


def test_link_preconditions(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)
    first = advance_to_active(
        compliance_document_draft(shelf.document_type, code="ПОТБ-1"), shelf.document_type
    )
    second = advance_to_active(
        compliance_document_draft(shelf.document_type, code="ПОТБ-2"), shelf.document_type
    )
    employee_type = make_document_type(
        organization_id=shelf.organization_id,
        code="employee_card",
        subject_kind=DocumentSubjectKind.EMPLOYEE,
    )
    shelf.document_types.add(employee_type)
    employee_document = compliance_document_draft(
        employee_type, code="ЛК-1", subject_id=uuid4()
    )
    foreign = compliance_document_draft(organization_id=OrganizationId(value=uuid4()))
    for document in (first, second, employee_document, foreign):
        shelf.documents.add(document)

    def link(document_id: object, version: int) -> Any:
        return shelf.post(
            f"/slots/{slot.id.value}/documents",
            {"document_id": str(document_id), "version": version},
        )

    assert link(first.id.value, 1).status_code == 200
    assert_error_envelope(
        link(second.id.value, 2), status_code=422, code="already_linked_active_document"
    )
    assert_error_envelope(
        link(employee_document.id.value, 2),
        status_code=422,
        code="document_subject_not_supported",
    )
    assert_error_envelope(
        link(foreign.id.value, 2), status_code=404, code="compliance_document_not_found"
    )
    assert_error_envelope(
        link(uuid4(), 2), status_code=404, code="compliance_document_not_found"
    )
    assert_error_envelope(
        link(second.id.value, 1), status_code=409, code="shelf_slot_version_conflict"
    )


# ---- tenancy ----


@pytest.mark.parametrize(
    ("suffix", "body"),
    [
        ("/exclude", {"reason": "other", "comment": COMMENT, "version": 1}),
        ("/restore", {"version": 1}),
        ("/confirm-applicable", {"version": 1}),
        ("/documents", {"document_id": str(uuid4()), "version": 1}),
        (f"/documents/{uuid4()}/unlink", {"version": 1}),
        ("/develop", {"version": 1}),
    ],
)
def test_commands_on_a_foreign_place_are_404(
    shelf: ShelfClient, suffix: str, body: dict[str, Any]
) -> None:
    foreign_section = make_section(organization_id=OrganizationId(value=uuid4()))
    shelf.sections.add(foreign_section)
    foreign = make_slot(foreign_section, curated_status=CuratedSlotStatus.TO_CLARIFY)
    shelf.slots.add(foreign)

    response = shelf.post(f"/slots/{foreign.id.value}{suffix}", body)

    assert_error_envelope(response, status_code=404, code="shelf_slot_not_found")
    stored = shelf.slots.get(foreign.organization_id, foreign.id)
    assert stored is not None and stored.version == 1


def test_patch_on_a_foreign_place_is_404(shelf: ShelfClient) -> None:
    foreign_section = make_section(organization_id=OrganizationId(value=uuid4()))
    shelf.sections.add(foreign_section)
    foreign = make_slot(foreign_section)
    shelf.slots.add(foreign)

    response = shelf.patch(f"/slots/{foreign.id.value}", {"version": 1, "notes": "x"})

    assert_error_envelope(response, status_code=404, code="shelf_slot_not_found")
