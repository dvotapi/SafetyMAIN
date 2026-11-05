"""``develop``: draft document + link in one unit of work, two audit events (P7, P12)."""

from __future__ import annotations

from typing import Any

import pytest

from backend.core.domain.value_objects import Role
from backend.core.domain.value_objects.compliance_enums import DocumentSubjectKind
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
from backend.core.domain.value_objects.shelf_enums import CuratedSlotStatus
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.shelf_support import ShelfClient, build_shelf_client
from tests.fixtures.compliance_documents import (
    advance_to_active,
    compliance_document_draft,
    make_document_type,
)


@pytest.fixture
def shelf() -> ShelfClient:
    return build_shelf_client()


def _develop(shelf: ShelfClient, slot_id: object, **body: Any) -> Any:
    return shelf.post(f"/slots/{slot_id}/develop", {"version": 1, **body})


def test_develop_creates_and_links_a_draft_atomically(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, document_type_code="transport_plan")

    response = _develop(shelf, slot.id.value)

    assert response.status_code == 201
    body = response.json()
    document = shelf.documents.get(shelf.organization_id, _document_id(body))
    assert document is not None
    assert document.status.value == "draft"
    assert document.code == slot.code.value
    assert document.title == slot.title
    assert document.source.value == "manual"
    assert response.headers["Location"].endswith(f"/compliance-documents/{body['document_id']}")
    assert body["slot"]["effective_status"] == "in_progress"
    assert body["slot"]["primary_action"] == "open_project"
    assert [edition["id"] for edition in body["slot"]["editions"]] == [body["document_id"]]
    stored = shelf.slots.get(shelf.organization_id, slot.id)
    assert stored is not None and stored.version == 2
    (created,) = shelf.events("compliance.document.created")
    (linked,) = shelf.events("compliance.place.linked")
    assert created.metadata["document_id"] == body["document_id"]
    assert linked.metadata["document_id"] == body["document_id"]
    assert linked.metadata["slot_code"] == slot.code.value


def test_request_type_overrides_the_place_type(shelf: ShelfClient) -> None:
    other = make_document_type(organization_id=shelf.organization_id, code="order")
    shelf.document_types.add(other)
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, document_type_code="transport_plan")

    body = _develop(shelf, slot.id.value, document_type_code="order").json()

    document = shelf.documents.get(shelf.organization_id, _document_id(body))
    assert document is not None and document.document_type_id == other.id


def test_develop_without_any_type_is_rejected(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)

    assert_error_envelope(
        _develop(shelf, slot.id.value), status_code=422, code="document_type_required"
    )
    _assert_nothing_written(shelf, slot)


def test_develop_with_an_inactive_type_is_rejected(shelf: ShelfClient) -> None:
    shelf.document_types.add(
        make_document_type(
            organization_id=shelf.organization_id, code="retired", is_active=False
        )
    )
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)

    assert_error_envelope(
        _develop(shelf, slot.id.value, document_type_code="retired"),
        status_code=422,
        code="document_type_not_found",
    )
    _assert_nothing_written(shelf, slot)


def test_develop_with_a_non_organization_type_writes_nothing(shelf: ShelfClient) -> None:
    shelf.document_types.add(
        make_document_type(
            organization_id=shelf.organization_id,
            code="vehicle_card",
            subject_kind=DocumentSubjectKind.ASSET,
        )
    )
    section = shelf.seed_section()
    slot = shelf.seed_slot(section)

    response = _develop(shelf, slot.id.value, document_type_code="vehicle_card")

    assert response.status_code == 422
    _assert_nothing_written(shelf, slot)


def test_develop_is_rejected_while_a_document_is_held(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, document_type_code="transport_plan")
    active = advance_to_active(
        compliance_document_draft(shelf.document_type, code="ПОТБ-1"), shelf.document_type
    )
    shelf.documents.add(active)
    linked = shelf.post(
        f"/slots/{slot.id.value}/documents",
        {"document_id": str(active.id.value), "version": 1},
    )
    assert linked.status_code == 200

    response = shelf.post(f"/slots/{slot.id.value}/develop", {"version": 2})

    assert_error_envelope(response, status_code=422, code="already_linked_active_document")


def test_develop_on_an_excluded_place_and_stale_version(shelf: ShelfClient) -> None:
    section = shelf.seed_section()
    slot = shelf.seed_slot(section, document_type_code="transport_plan")

    assert_error_envelope(
        shelf.post(f"/slots/{slot.id.value}/develop", {"version": 3}),
        status_code=409,
        code="shelf_slot_version_conflict",
    )
    excluded = shelf.post(
        f"/slots/{slot.id.value}/exclude",
        {"reason": "other", "comment": "Не требуется", "version": 1},
    )
    assert excluded.status_code == 200
    assert_error_envelope(
        shelf.post(f"/slots/{slot.id.value}/develop", {"version": 2}),
        status_code=422,
        code="already_excluded",
    )


def test_develop_requires_document_create_permission() -> None:
    member = build_shelf_client(role=Role.member())
    section = member.seed_section()
    slot = member.seed_slot(section, curated_status=CuratedSlotStatus.MISSING)

    response = _develop(member, slot.id.value)

    assert_error_envelope(response, status_code=403, code="permission_denied")


def _document_id(body: dict[str, Any]) -> ComplianceDocumentId:
    return ComplianceDocumentId(value=body["document_id"])


def _assert_nothing_written(shelf: ShelfClient, slot: Any) -> None:
    stored = shelf.slots.get(shelf.organization_id, slot.id)
    assert stored is not None and stored.version == slot.version
    assert stored.linked_document_ids == ()
    assert all(
        document.code != slot.code.value for document in shelf.documents.snapshot().values()
    )
    assert not [e for e in shelf.events("compliance.document.created") if not e.failure_code]

