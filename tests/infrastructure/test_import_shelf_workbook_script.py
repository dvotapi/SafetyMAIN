"""``scripts/import_shelf_workbook.py`` on synthetic workbooks (in memory and PostgreSQL)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from backend.core.application.exceptions.authorization import PermissionDeniedError
from backend.core.application.services.shelf_import_mapping import H_KIND, H_STATUS
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
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
from backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model import (
    AuditEventModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from backend.core.infrastructure.time.utc_clock import UtcClock
from scripts.import_shelf_workbook import (
    EXIT_REFUSED,
    EXIT_REJECTED,
    ImportRefused,
    exit_code,
    format_report,
    main,
    run_import,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization
from tests.fixtures.shelf_workbook import place_row, write_workbook

pytest_plugins = ("tests.infrastructure.db_fixtures",)

ROWS = [
    place_row("ТрБ.01.01"),
    place_row("ТрБ.01.02", **{H_STATUS: "Не применимо"}),
    place_row("ПожБ.01.01"),
]


class _Authorization:
    """Stand-in for ``AuthorizationService``: only listed users may curate."""

    def __init__(self, curators: set[UserId]) -> None:
        self.curators = curators

    def require_permission(self, *, actor_user_id: UserId, organization_id: Any, permission: Any) -> None:
        if actor_user_id not in self.curators:
            raise PermissionDeniedError(
                user_id=actor_user_id, organization_id=organization_id, permission=permission
            )


class _Memory:
    def __init__(self) -> None:
        now = datetime.now(UTC)
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
        self.curator = self._user("curator@example.com", UserStatus.ACTIVE)
        self.viewer = self._user("viewer@example.com", UserStatus.ACTIVE)
        self._user("gone@example.com", UserStatus.DEACTIVATED)
        self.slots = InMemoryShelfSlotRepository()
        self.audit = InMemoryAuditEventRepository()
        self.repositories: dict[str, Any] = {
            "organizations": self.organizations,
            "users": self.users,
            "document_types": InMemoryDocumentTypeRepository(),
            "compliance_documents": InMemoryComplianceDocumentRepository(),
            "shelf_sections": InMemoryShelfSectionRepository(),
            "shelf_slots": self.slots,
            "audit_events": self.audit,
        }
        self.authorization = _Authorization({self.curator})

    def _user(self, email: str, status: UserStatus) -> UserId:
        now = datetime.now(UTC)
        user_id = UserId(value=uuid4())
        self.users.add(
            User(
                id=user_id,
                email=email,
                display_name=email,
                status=status,
                created_at=now,
                updated_at=now,
            )
        )
        return user_id

    def uow(self) -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(**self.repositories)

    def run(self, path: Path, *, email: str = "curator@example.com", dry_run: bool = False, organization: OrganizationId | None = None) -> Any:
        return run_import(
            uow_factory=self.uow,
            authorization=self.authorization,  # type: ignore[arg-type]
            clock=UtcClock(),
            organization_id=organization or self.organization_id,
            path=path,
            actor_email=email,
            dry_run=dry_run,
        )


def test_dry_run_then_real_run_then_idempotent_rerun(tmp_path: Path) -> None:
    memory = _Memory()
    path = write_workbook(tmp_path / "shelf.xlsx", ROWS)

    dry = memory.run(path, dry_run=True)
    assert len(dry.created) == 3 and not dry.applied
    assert memory.slots.list_all(memory.organization_id) == ()

    real = memory.run(path)
    assert real.applied and len(real.created) == 3 and real.excluded_total == 1
    assert exit_code(real) == 0

    again = memory.run(path)
    assert len(again.unchanged) == 3
    imported = [e for e in memory.audit.snapshot().values() if e.action.value == "compliance.shelf.imported"]
    assert len(imported) == 2
    assert {e.actor_user_id for e in imported} == {memory.curator}
    text = format_report(again)
    assert "unchanged 3" in text and "3 places, 2 sections" in text


def test_rejected_rows_exit_1_and_write_nothing(tmp_path: Path) -> None:
    memory = _Memory()
    path = write_workbook(tmp_path / "shelf.xlsx", [*ROWS, place_row("ТрБ.01.03", **{H_KIND: "Письмо"})])

    report = memory.run(path)

    assert exit_code(report) == EXIT_REJECTED
    assert memory.slots.list_all(memory.organization_id) == ()
    assert "row 7, «Вид» = «Письмо»: unknown value" in format_report(report)


@pytest.mark.parametrize(
    ("email", "organization", "message"),
    [
        ("nobody@example.com", None, "No user"),
        ("gone@example.com", None, "not active"),
        ("viewer@example.com", None, "may not curate"),
        ("curator@example.com", OrganizationId(value=uuid4()), "Organization not found"),
    ],
)
def test_refused_actors(tmp_path: Path, email: str, organization: OrganizationId | None, message: str) -> None:
    memory = _Memory()
    path = write_workbook(tmp_path / "shelf.xlsx", ROWS)

    with pytest.raises(ImportRefused, match=message):
        memory.run(path, email=email, organization=organization)


def test_unreadable_file_is_refused(tmp_path: Path) -> None:
    memory = _Memory()

    with pytest.raises(ImportRefused, match="not found"):
        memory.run(tmp_path / "absent.xlsx")


def test_main_requires_database_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    code = main(
        [
            "--organization-id",
            str(uuid4()),
            "--file",
            str(tmp_path / "x.xlsx"),
            "--actor-email",
            "a@example.com",
        ]
    )

    assert code == EXIT_REFUSED


@pytest.mark.db
def test_main_against_postgresql_twice(
    sqlalchemy_session_factory: sessionmaker,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    organization_id = OrganizationId(value=uuid4())
    curator = UserId(value=uuid4())
    now = datetime.now(UTC)
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        ensure_organization(uow.session, organization_id)
        uow.users.add(
            User(
                id=curator,
                email="shelf-curator@example.com",
                display_name="Куратор",
                status=UserStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        uow.session.flush()
        uow.memberships.add(
            Membership(
                id=MembershipId(value=uuid4()),
                user_id=curator,
                organization_id=organization_id,
                status=MembershipStatus.ACTIVE,
                role=Role.admin(),
                joined_at=now,
                updated_at=now,
            )
        )
        uow.commit()
    path = write_workbook(tmp_path / "shelf.xlsx", ROWS)
    report_path = tmp_path / "report.json"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-sufficient-length")
    args = [
        "--organization-id",
        str(organization_id.value),
        "--file",
        str(path),
        "--actor-email",
        "shelf-curator@example.com",
        "--report",
        str(report_path),
    ]

    assert main(args) == 0
    assert "created 3" in capsys.readouterr().out
    assert main(args) == 0
    assert "unchanged 3" in capsys.readouterr().out

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["unchanged"]) == 3
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        assert len(uow.shelf_slots.list_all(organization_id)) == 3
        assert [s.code for s in uow.shelf_sections.list(organization_id)] == ["ПожБ", "ТрБ"]
        imported = uow.session.scalar(
            select(func.count())
            .select_from(AuditEventModel)
            .where(
                AuditEventModel.target_organization_id == organization_id.value,
                AuditEventModel.action == "compliance.shelf.imported",
            )
        )
    assert imported == 2

