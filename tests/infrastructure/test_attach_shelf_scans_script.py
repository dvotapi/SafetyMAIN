"""``scripts/attach_shelf_scans.py`` on synthetic files and in-memory storage (§4.5)."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from backend.core.application.exceptions.authorization import PermissionDeniedError
from backend.core.contracts.storage import PresignedUpload
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryComplianceDocumentRepository,
    InMemoryDocumentTypeRepository,
    InMemoryOrganizationRepository,
    InMemoryShelfSectionRepository,
    InMemoryShelfSlotRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from backend.core.infrastructure.storage.in_memory_storage import InMemoryStorage
from backend.core.infrastructure.time.utc_clock import UtcClock
from scripts.attach_shelf_scans import (
    EXIT_FAILED,
    AttachRefused,
    exit_code,
    format_report,
    make_locator,
    run_attach,
)
from tests.fixtures.compliance_documents import make_document_type
from tests.fixtures.shelf import make_section, make_slot

PDF = b"%PDF-1.4\n% synthetic scan\n%%EOF\n"
EFFECTIVE = date(2026, 11, 6)


class _Authorization:
    def __init__(self, allowed: set[UserId]) -> None:
        self.allowed = allowed

    def require_permission(self, *, actor_user_id: UserId, organization_id: Any, permission: Any) -> None:
        if actor_user_id not in self.allowed:
            raise PermissionDeniedError(
                user_id=actor_user_id, organization_id=organization_id, permission=permission
            )


class _World:
    def __init__(self, root: Path) -> None:
        now = datetime.now(UTC)
        self.root = root
        self.organization_id = OrganizationId(value=uuid4())
        self.organizations = InMemoryOrganizationRepository()
        self.organizations.add(
            Organization(
                id=self.organization_id,
                name="Синтетика",
                status=OrganizationStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        self.users = InMemoryUserRepository()
        self.curator = UserId(value=uuid4())
        self.users.add(
            User(
                id=self.curator,
                email="curator@example.com",
                display_name="Куратор",
                status=UserStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        self.types = InMemoryDocumentTypeRepository()
        self.types.add(make_document_type(organization_id=self.organization_id, code="plan"))
        self.types.add(
            make_document_type(
                organization_id=self.organization_id,
                code="ordered",
                requires_approval_order=True,
            )
        )
        self.documents = InMemoryComplianceDocumentRepository()
        self.sections = InMemoryShelfSectionRepository()
        self.slots = InMemoryShelfSlotRepository()
        self.audit = InMemoryAuditEventRepository()
        self.section = make_section(
            organization_id=self.organization_id,
            subsections=tuple((f"{n:02d}", f"П{n}") for n in range(1, 4)),
        )
        self.sections.add(self.section)
        self.storage = InMemoryStorage(
            bucket="b", presign_ttl_seconds=600, max_upload_bytes=1024 * 1024, clock=UtcClock()
        )
        self.puts: list[str] = []
        self.authorization = _Authorization({self.curator})

    def uow(self) -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            organizations=self.organizations,
            users=self.users,
            document_types=self.types,
            compliance_documents=self.documents,
            shelf_sections=self.sections,
            shelf_slots=self.slots,
            audit_events=self.audit,
        )

    def put(self, presigned: PresignedUpload, data: bytes) -> None:
        self.puts.append(presigned.key)
        self.storage.store_object(
            presigned.key,
            size_bytes=len(data),
            content_type="application/pdf",
            sha256=hashlib.sha256(data).hexdigest(),
        )

    def slot(self, code: str, **kwargs: Any) -> Any:
        defaults: dict[str, Any] = {
            "curated_status": CuratedSlotStatus.PRESENT,
            "document_type_code": "plan",
        }
        slot = make_slot(self.section, code=code, created_by=self.curator, **{**defaults, **kwargs})
        self.slots.add(slot)
        return slot

    def file(self, relative: str, data: bytes = PDF) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def run(self, *, apply: bool = True, **kwargs: Any) -> Any:
        return run_attach(
            uow_factory=self.uow,
            authorization=self.authorization,  # type: ignore[arg-type]
            clock=UtcClock(),
            storage=self.storage,
            max_upload_bytes=1024 * 1024,
            organization_id=self.organization_id,
            root=self.root,
            actor_email=kwargs.pop("actor_email", "curator@example.com"),
            apply=apply,
            effective_from=kwargs.pop("effective_from", EFFECTIVE),
            put=self.put,
            **kwargs,
        )

    def actions(self) -> list[str]:
        return [event.action.value for event in self.audit.snapshot().values()]


@pytest.fixture
def world(tmp_path: Path) -> _World:
    root = tmp_path / "scans"
    root.mkdir()
    return _World(root)


def test_attaches_a_pdf_end_to_end_and_reruns_as_skipped(world: _World) -> None:
    world.file("009/plan.pdf")
    slot = world.slot("ТрБ.01.01", legacy_location="009/plan.pdf")

    report = world.run()

    assert [item.code for item in report.attached] == ["ТрБ.01.01"]
    stored = world.slots.get(world.organization_id, slot.id)
    assert stored is not None and len(stored.linked_document_ids) == 1
    document = world.documents.get(world.organization_id, stored.linked_document_ids[0])
    assert document is not None
    assert document.status is ComplianceDocumentStatus.ACTIVE
    assert document.effective_from == EFFECTIVE
    assert document.code == "ТрБ.01.01"
    assert document.current_file is not None
    assert document.current_file.sha256 == hashlib.sha256(PDF).hexdigest()
    assert (world.root / "009/plan.pdf").read_bytes() == PDF
    for action in (
        "compliance.document.created",
        "compliance.place.linked",
        "compliance.document.updated",
        "compliance.document.file_attached",
        "compliance.document.approved",
        "compliance.document.activated",
    ):
        assert action in world.actions()

    again = world.run()
    assert again.attached == []
    assert [(item.code, item.reason) for item in again.skipped] == [("ТрБ.01.01", "has_document")]


def test_a_folder_with_exactly_one_pdf_is_used(world: _World) -> None:
    world.file("папка 009/scan.pdf")
    world.file("папка 009/readme.txt", b"x")
    world.slot("ТрБ.01.01", legacy_location="папка 009")

    assert [item.code for item in world.run().attached] == ["ТрБ.01.01"]


def test_dry_run_writes_nothing(world: _World) -> None:
    world.file("plan.pdf")
    world.slot("ТрБ.01.01", legacy_location="plan.pdf")

    report = world.run(apply=False, effective_from=None)

    assert report.candidates == ["ТрБ.01.01"]
    assert world.documents.snapshot() == {}
    assert world.puts == []
    assert world.audit.snapshot() == {}
    assert "DRY RUN" in format_report(report)


def test_skip_reasons(world: _World, tmp_path: Path) -> None:
    world.file("two/a.pdf")
    world.file("two/b.pdf")
    world.file("fake.pdf", b"not a pdf")
    world.file("notes.txt", b"x")
    (tmp_path / "secret.pdf").write_bytes(PDF)
    world.file("big.pdf", PDF + b"0" * (1024 * 1024))
    world.slot("ТрБ.01.01", curated_status=CuratedSlotStatus.MISSING, legacy_location="x")
    excluded = world.slot("ТрБ.01.02", legacy_location="x")
    world.slots.save(
        excluded.exclude(
            reason=SlotExclusionReason.OTHER,
            comment="Не нужно",
            at=excluded.created_at,
            actor_id=world.curator,
            expected_version=1,
        ),
        expected_version=1,
    )
    world.slot("ТрБ.01.03", document_type_code=None, legacy_location="x")
    world.slot("ТрБ.01.04", document_type_code="unknown", legacy_location="x")
    world.slot("ТрБ.01.05", document_type_code="ordered", legacy_location="x")
    world.slot("ТрБ.02.01", legacy_location="")
    world.slot("ТрБ.02.02", legacy_location="missing.pdf")
    world.slot("ТрБ.02.03", legacy_location="two")
    world.slot("ТрБ.02.04", legacy_location="fake.pdf")
    world.slot("ТрБ.02.05", legacy_location="notes.txt")
    world.slot("ТрБ.03.01", legacy_location="../secret.pdf")
    world.slot("ТрБ.03.02", legacy_location="big.pdf")

    report = world.run(apply=False, effective_from=None)

    assert {item.code: item.reason for item in report.skipped} == {
        "ТрБ.01.01": "not_present",
        "ТрБ.01.02": "excluded",
        "ТрБ.01.03": "no_document_type",
        "ТрБ.01.04": "type_not_found",
        "ТрБ.01.05": "type_requires_approval_order",
        "ТрБ.02.01": "no_location",
        "ТрБ.02.02": "file_not_found",
        "ТрБ.02.03": "ambiguous",
        "ТрБ.02.04": "not_pdf",
        "ТрБ.02.05": "not_pdf",
        "ТрБ.03.01": "outside_root",
        "ТрБ.03.02": "too_large",
    }
    assert report.candidates == []


def test_symlink_out_of_the_root_is_refused(world: _World, tmp_path: Path) -> None:
    (tmp_path / "outside.pdf").write_bytes(PDF)
    (world.root / "link.pdf").symlink_to(tmp_path / "outside.pdf")

    assert make_locator(world.root, 10_000)("link.pdf").reason is not None


def test_failure_at_confirm_keeps_a_linked_draft_and_continues(world: _World) -> None:
    world.file("a.pdf")
    world.file("b.pdf")
    first = world.slot("ТрБ.01.01", legacy_location="a.pdf")
    world.slot("ТрБ.01.02", legacy_location="b.pdf")
    calls = {"n": 0}
    original = world.put

    def flaky(presigned: PresignedUpload, data: bytes) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            return  # the PUT "succeeds" but nothing lands in storage
        original(presigned, data)

    world.put = flaky  # type: ignore[method-assign]
    report = world.run()

    assert [(item.code, item.failed_step) for item in report.failed] == [("ТрБ.01.01", "confirm")]
    assert [item.code for item in report.attached] == ["ТрБ.01.02"]
    assert exit_code(report) == EXIT_FAILED
    stored = world.slots.get(world.organization_id, first.id)
    assert stored is not None and len(stored.linked_document_ids) == 1
    draft = world.documents.get(world.organization_id, stored.linked_document_ids[0])
    assert draft is not None and draft.status is ComplianceDocumentStatus.DRAFT
    assert "finish it in the shelf" in format_report(report)


def test_limit_and_refusals(world: _World) -> None:
    world.file("a.pdf")
    world.file("b.pdf")
    world.slot("ТрБ.01.01", legacy_location="a.pdf")
    world.slot("ТрБ.01.02", legacy_location="b.pdf")

    assert [item.code for item in world.run(limit=1).attached] == ["ТрБ.01.01"]
    with pytest.raises(AttachRefused, match="effective-from"):
        world.run(effective_from=None)
    with pytest.raises(AttachRefused, match="No user"):
        world.run(actor_email="nobody@example.com")
    world.authorization.allowed = set()
    with pytest.raises(AttachRefused, match="lacks shelf:curate"):
        world.run()


pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
def test_attach_against_postgresql(sqlalchemy_session_factory: Any, tmp_path: Path) -> None:
    from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
        SQLAlchemyUnitOfWork,
    )
    from tests.contracts.sqlalchemy_identity_seed import (
        ensure_organization,
        ensure_user,
    )

    root = tmp_path / "scans"
    root.mkdir()
    (root / "plan.pdf").write_bytes(PDF)
    organization_id = OrganizationId(value=uuid4())
    curator = UserId(value=uuid4())

    def uow() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(sqlalchemy_session_factory)

    section = make_section(organization_id=organization_id)
    slot = make_slot(
        section,
        code="ТрБ.01.01",
        created_by=curator,
        curated_status=CuratedSlotStatus.PRESENT,
        document_type_code="plan",
        legacy_location="plan.pdf",
    )
    with uow() as seed:
        ensure_organization(seed.session, organization_id)
        ensure_user(seed.session, curator)
        seed.document_types.add(make_document_type(organization_id=organization_id, code="plan"))
        seed.shelf_sections.add(section)
        seed.shelf_slots.add(slot)
        seed.commit()
    with uow() as read:
        email = read.users.get(curator).email
    storage = InMemoryStorage(
        bucket="b", presign_ttl_seconds=600, max_upload_bytes=1024 * 1024, clock=UtcClock()
    )

    def put(presigned: PresignedUpload, data: bytes) -> None:
        storage.store_object(
            presigned.key,
            size_bytes=len(data),
            content_type="application/pdf",
            sha256=hashlib.sha256(data).hexdigest(),
        )

    report = run_attach(
        uow_factory=uow,
        authorization=_Authorization({curator}),  # type: ignore[arg-type]
        clock=UtcClock(),
        storage=storage,
        max_upload_bytes=1024 * 1024,
        organization_id=organization_id,
        root=root,
        actor_email=email,
        apply=True,
        effective_from=EFFECTIVE,
        put=put,
    )

    assert [item.code for item in report.attached] == ["ТрБ.01.01"], report.failed
    with uow() as check:
        stored = check.shelf_slots.get(organization_id, slot.id)
        assert stored is not None
        document = check.compliance_documents.get(organization_id, stored.linked_document_ids[0])
        assert document is not None and document.status is ComplianceDocumentStatus.ACTIVE


# ---- signed editions approved by one order (plan 2026-11-06-p11-012-attach-signed-editions) ----


def _signed_world(world: _World) -> None:
    world.types.add(make_document_type(organization_id=world.organization_id, code="order"))
    world.types.add(
        make_document_type(
            organization_id=world.organization_id,
            code="iot_profession",
            requires_approval_order=True,
        )
    )
    world.slot("ТрБ.01.01", document_type_code="order")
    world.slot("ТрБ.01.02", document_type_code="iot_profession")
    world.slot(
        "ТрБ.01.03",
        document_type_code="iot_profession",
        curated_status=CuratedSlotStatus.IN_PROGRESS,
    )
    world.file("ТрБ.01.01 Приказ о введении инструкций.pdf")
    world.file("ТрБ.01.02 ИОТ для водителя.pdf")
    world.file("ТрБ.01.03 ИОТ для взрывника.pdf")


def _document_of(world: _World, code: str) -> Any:
    slot = world.slots.get_by_code(world.organization_id, code)
    assert slot is not None and slot.linked_document_ids
    return world.documents.get(world.organization_id, slot.linked_document_ids[-1])


def test_order_first_then_instructions_approved_by_it(world: _World) -> None:
    _signed_world(world)

    report = world.run(
        match_by_code=True, approval_order="ТрБ.01.01", order_note="№ 7-ТЕСТ от 01.02.2026"
    )

    assert [item.code for item in report.attached] == ["ТрБ.01.01", "ТрБ.01.02", "ТрБ.01.03"]
    order = _document_of(world, "ТрБ.01.01")
    assert order.status is ComplianceDocumentStatus.ACTIVE
    assert order.notes == "№ 7-ТЕСТ от 01.02.2026"
    for code in ("ТрБ.01.02", "ТрБ.01.03"):
        document = _document_of(world, code)
        assert document.status is ComplianceDocumentStatus.ACTIVE
        assert document.approved_by_document_id == order.id
        assert document.effective_from == EFFECTIVE
        assert document.current_signed_scan is not None
        assert document.current_file is not None

    again = world.run(match_by_code=True, approval_order="ТрБ.01.01")
    assert again.attached == [] and again.failed == []
    assert {item.code: item.reason for item in again.skipped} == {
        "ТрБ.01.02": "has_document",
        "ТрБ.01.03": "has_document",
    }


def test_existing_order_is_reused_on_a_later_run(world: _World) -> None:
    _signed_world(world)
    world.run(match_by_code=True, approval_order="ТрБ.01.01", limit=1)
    order = _document_of(world, "ТрБ.01.01")

    report = world.run(match_by_code=True, approval_order="ТрБ.01.01")

    assert [item.code for item in report.attached] == ["ТрБ.01.03"]
    assert _document_of(world, "ТрБ.01.03").approved_by_document_id == order.id


def test_order_failure_stops_the_run(world: _World) -> None:
    _signed_world(world)
    world.put = lambda presigned, data: None  # type: ignore[method-assign,assignment]

    report = world.run(match_by_code=True, approval_order="ТрБ.01.01")

    assert [(item.code, item.failed_step) for item in report.failed] == [("ТрБ.01.01", "confirm")]
    assert report.attached == []
    assert {item.reason for item in report.skipped} == {"order_failed"}
    for code in ("ТрБ.01.02", "ТрБ.01.03"):
        slot = world.slots.get_by_code(world.organization_id, code)
        assert slot is not None and slot.linked_document_ids == ()


def test_code_matching_reports_unknown_ambiguous_and_missing_order(world: _World) -> None:
    _signed_world(world)
    world.file("ТрБ.01.02 ИОТ для водителя (копия).pdf")
    world.file("ТрБ.03.09 Лишний.pdf")
    world.file("Без кода.pdf")

    report = world.run(apply=False, effective_from=None, match_by_code=True, approval_order="ТрБ.09.09")

    reasons = {(item.code or item.detail): item.reason for item in report.skipped}
    assert reasons["ТрБ.01.02"] == "ambiguous"
    assert reasons["ТрБ.03.09"] == "unknown_code"
    assert reasons["Без кода.pdf"] == "no_code_in_name"
    assert reasons["ТрБ.09.09"] == "order_file_not_found"
    assert reasons["ТрБ.01.03"] == "order_not_in_force"
    assert report.candidates == ["ТрБ.01.01"]
    assert world.documents.snapshot() == {}


def test_without_an_order_types_that_need_one_are_skipped(world: _World) -> None:
    _signed_world(world)

    report = world.run(apply=False, effective_from=None, match_by_code=True)

    assert report.candidates == ["ТрБ.01.01"]
    assert {item.code: item.reason for item in report.skipped} == {
        "ТрБ.01.02": "type_requires_approval_order",
        "ТрБ.01.03": "type_requires_approval_order",
    }
