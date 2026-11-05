"""Shelf read API: overview counts, one shelf, search, place detail, RBAC, tenancy."""

from __future__ import annotations

from urllib.parse import quote
from uuid import uuid4

import pytest

from backend.core.domain.value_objects import OrganizationId, Role
from backend.core.domain.value_objects.compliance_enums import SafetyDomain
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
    SlotObligationLevel,
)
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.shelf_support import ShelfClient, build_shelf_client
from tests.fixtures.compliance_documents import (
    advance_to_active,
    compliance_document_draft,
)
from tests.fixtures.shelf import make_section, make_slot


@pytest.fixture
def shelf() -> ShelfClient:
    return build_shelf_client()


def _seed_two_shelves(shelf: ShelfClient) -> None:
    """ТрБ: 4 places (present, missing, to_clarify, excluded); ПожБ: 1 in progress."""
    transport = shelf.seed_section(code="ТрБ", number=10)
    fire = shelf.seed_section(
        code="ПожБ",
        number=3,
        title="Пожарная безопасность",
        safety_domain=SafetyDomain.FIRE,
        subsections=(("01", "Общие"),),
    )
    active = advance_to_active(
        compliance_document_draft(shelf.document_type, code="ТрБ.01.01"),
        shelf.document_type,
    )
    shelf.documents.add(active)
    present = make_slot(transport, code="ТрБ.01.01", created_by=shelf.user_id)
    shelf.slots.add(
        present.link_document(
            document=active,
            linked_documents=(),
            at=present.created_at,
            actor_id=shelf.user_id,
            expected_version=1,
        )
    )
    shelf.seed_slot(transport, code="ТрБ.01.02")
    shelf.seed_slot(
        transport,
        code="ТрБ.02.01",
        curated_status=CuratedSlotStatus.TO_CLARIFY,
        obligation_level=SlotObligationLevel.CONDITIONAL,
    )
    excluded = make_slot(transport, code="ТрБ.02.02", created_by=shelf.user_id)
    shelf.slots.add(
        excluded.exclude(
            reason=SlotExclusionReason.NOT_APPLICABLE,
            comment="Нет объектов транспортной инфраструктуры",
            at=excluded.created_at,
            actor_id=shelf.user_id,
            expected_version=1,
        )
    )
    shelf.seed_slot(fire, code="ПожБ.01.01", curated_status=CuratedSlotStatus.IN_PROGRESS)


def test_overview_counts_and_readiness_match_the_evaluator(shelf: ShelfClient) -> None:
    _seed_two_shelves(shelf)

    response = shelf.get("")

    assert response.status_code == 200
    body = response.json()
    assert [section["code"] for section in body["sections"]] == ["ПожБ", "ТрБ"]
    transport = body["sections"][1]
    assert transport["total"] == 4
    assert transport["mandatory_total"] == 3
    assert transport["by_group"] == {
        "present": 1,
        "review": 0,
        "in_progress": 0,
        "missing": 1,
        "to_clarify": 1,
        "excluded": 1,
    }
    assert transport["readiness_percent"] == 50
    assert [item["code"] for item in transport["strip"]] == [
        "ТрБ.01.01",
        "ТрБ.01.02",
        "ТрБ.02.01",
        "ТрБ.02.02",
    ]
    assert [item["group"] for item in transport["strip"]] == [
        "present",
        "missing",
        "to_clarify",
        "excluded",
    ]
    assert body["totals"]["places"] == 5
    assert body["totals"]["excluded"] == 1
    assert body["totals"]["by_group"]["in_progress"] == 1
    assert body["totals"]["readiness_percent"] == 40
    assert "evaluated_at" in body


def test_overview_of_an_empty_shelf(shelf: ShelfClient) -> None:
    body = shelf.get("").json()

    assert body["sections"] == []
    assert body["totals"]["places"] == 0
    assert body["totals"]["readiness_percent"] == 0


def test_section_slots_are_grouped_by_subsection_with_cyrillic_path(
    shelf: ShelfClient,
) -> None:
    _seed_two_shelves(shelf)

    response = shelf.get(f"/sections/{quote('ТрБ')}/slots")

    assert response.status_code == 200
    body = response.json()
    assert body["section"] == {
        "code": "ТрБ",
        "number": 10,
        "title": "Транспортная безопасность",
    }
    assert [item["code"] for item in body["subsections"]] == ["ТрБ.01", "ТрБ.02"]
    first = body["subsections"][0]["slots"][0]
    assert first["code"] == "ТрБ.01.01"
    assert first["subsection_code"] == "ТрБ.01"
    assert first["effective_status"] == "present"
    assert first["group"] == "present"
    assert first["has_acknowledgement_gap"] is False
    excluded = body["subsections"][1]["slots"][1]
    assert excluded["effective_status"] == "excluded"


def test_unknown_section_is_404(shelf: ShelfClient) -> None:
    assert_error_envelope(
        shelf.get(f"/sections/{quote('ЭкоБ')}/slots"),
        status_code=404,
        code="shelf_section_not_found",
    )


def test_search_matches_code_and_title_case_insensitively(shelf: ShelfClient) -> None:
    _seed_two_shelves(shelf)

    by_code = shelf.get("/slots", params={"q": "трб.02"}).json()["items"]
    by_title = shelf.get("/slots", params={"q": "ПЛАН ОБЕСПЕЧЕНИЯ", "limit": 2}).json()[
        "items"
    ]

    assert [item["code"] for item in by_code] == ["ТрБ.02.01", "ТрБ.02.02"]
    assert len(by_title) == 2


@pytest.mark.parametrize(
    "params",
    [{}, {"q": ""}, {"q": "x" * 101}, {"q": "ТрБ", "limit": 0}, {"q": "ТрБ", "limit": 101}],
)
def test_search_rejects_invalid_parameters(shelf: ShelfClient, params: dict) -> None:
    assert shelf.get("/slots", params=params).status_code == 422


def test_slot_detail_shows_current_document_editions_and_actions(
    shelf: ShelfClient,
) -> None:
    _seed_two_shelves(shelf)
    slot = shelf.slots.get_by_code(shelf.organization_id, "ТрБ.01.01")
    assert slot is not None

    body = shelf.get(f"/slots/{slot.id.value}").json()

    assert body["effective_status"] == "present"
    assert body["current_document"]["code"] == "ТрБ.01.01"
    assert body["current_document"]["status"] == "active"
    assert body["current_document"]["signed_scan"] is None
    assert body["current_document"]["working_file"]["content_type"] == "application/pdf"
    assert [edition["status"] for edition in body["editions"]] == ["active"]
    assert body["primary_action"] == "open_document"
    assert body["available_actions"] == ["open_document", "exclude"]
    assert body["acknowledgement"] is None
    assert body["review_date"] is not None
    assert body["version"] == 2


def test_excluded_slot_detail_names_who_excluded_it(shelf: ShelfClient) -> None:
    _seed_two_shelves(shelf)
    slot = shelf.slots.get_by_code(shelf.organization_id, "ТрБ.02.02")
    assert slot is not None

    body = shelf.get(f"/slots/{slot.id.value}").json()

    assert body["exclusion"]["reason"] == "not_applicable"
    assert body["exclusion"]["excluded_by_name"] == "Куратор Полки"
    assert body["primary_action"] == "restore"
    assert body["available_actions"] == ["restore"]


def test_slot_of_another_organization_is_404(shelf: ShelfClient) -> None:
    foreign_section = make_section(organization_id=OrganizationId(value=uuid4()))
    shelf.sections.add(foreign_section)
    foreign = make_slot(foreign_section)
    shelf.slots.add(foreign)

    assert_error_envelope(
        shelf.get(f"/slots/{foreign.id.value}"), status_code=404, code="shelf_slot_not_found"
    )
    assert shelf.get("").json()["sections"] == []


@pytest.mark.parametrize("role", [Role.member(), Role.auditor()])
def test_member_and_auditor_read_without_curator_actions(role: Role) -> None:
    viewer = build_shelf_client(role=role)
    _seed_two_shelves(viewer)
    present = viewer.slots.get_by_code(viewer.organization_id, "ТрБ.01.01")
    missing = viewer.slots.get_by_code(viewer.organization_id, "ТрБ.01.02")
    assert present is not None and missing is not None

    assert viewer.get("").status_code == 200
    present_body = viewer.get(f"/slots/{present.id.value}").json()
    missing_body = viewer.get(f"/slots/{missing.id.value}").json()

    assert present_body["available_actions"] == ["open_document"]
    assert missing_body["available_actions"] == []
    assert missing_body["primary_action"] is None


@pytest.mark.parametrize("role", [Role.member(), Role.auditor()])
def test_non_curators_cannot_change_places(role: Role) -> None:
    viewer = build_shelf_client(role=role)
    section = viewer.seed_section()
    slot = viewer.seed_slot(section)

    response = viewer.post(f"/slots/{slot.id.value}/confirm-applicable", {"version": 1})

    assert_error_envelope(response, status_code=403, code="permission_denied")
    denials = viewer.events("authorization.permission_denied")
    assert denials and denials[-1].resource_type.value == "SHELF_PLACE"


def test_shelf_requires_authentication(shelf: ShelfClient) -> None:
    response = shelf.client.get("/api/v1/shelf")

    assert response.status_code == 401
