"""Import the curated shelf workbook («Полка документов», TASK-P11-012 §3).

Runs through the application handlers: same domain rules and audit events as the
API, with the given curator as the actor. Re-running is idempotent; places edited
in SafetyMAIN since the previous import are reported as conflicts and never
overwritten (D3). Curator guide: ``docs/guides/ShelfImport.md``.

Usage (needs the ``import`` extra and the backend environment, DATABASE_URL set):

    python -m scripts.import_shelf_workbook \\
        --organization-id <uuid> --file shelf.xlsx --actor-email curator@example.com \\
        [--dry-run] [--report report.json]

Exit codes: 0 done, 1 the workbook has rejected rows (nothing written),
2 the run was refused (actor, organization, file).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
)
from backend.core.application.authorization.authorization_service import (
    AuthorizationService,
)
from backend.core.application.authorization.policies.resource_permissions import (
    SHELF_CURATE,
)
from backend.core.application.commands.shelf import ImportShelfWorkbookCommand
from backend.core.application.exceptions.authorization import AuthorizationError
from backend.core.application.handlers.shelf import (
    ImportReport,
    ImportShelfWorkbookHandler,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.user import UserStatus
from backend.core.domain.exceptions.organization import OrganizationNotFound
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.infrastructure.importing.shelf_workbook_reader import (
    WorkbookReadError,
    read_shelf_workbook,
)

EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_REFUSED = 2


class ImportRefused(Exception):
    """The run cannot start; the message is shown to the operator."""


def resolve_actor(
    uow_factory: Callable[[], UnitOfWorkContract],
    authorization: AuthorizationService,
    *,
    organization_id: OrganizationId,
    actor_email: str,
) -> UserId:
    """The actor must be an active user holding ``shelf:curate`` in the organization."""
    with uow_factory() as unit_of_work:
        try:
            unit_of_work.organizations.get(organization_id)
        except OrganizationNotFound as error:
            raise ImportRefused(f"Organization not found: {organization_id.value}.") from error
        user = unit_of_work.users.get_by_email(actor_email)
    if user is None:
        raise ImportRefused(f"No user with email {actor_email}.")
    if user.status is not UserStatus.ACTIVE:
        raise ImportRefused(f"User {actor_email} is not active.")
    try:
        authorization.require_permission(
            actor_user_id=user.id, organization_id=organization_id, permission=SHELF_CURATE
        )
    except AuthorizationError as error:
        raise ImportRefused(
            f"User {actor_email} may not curate the shelf of this organization."
        ) from error
    return user.id


def run_import(
    *,
    uow_factory: Callable[[], UnitOfWorkContract],
    authorization: AuthorizationService,
    clock: ClockContract,
    organization_id: OrganizationId,
    path: Path,
    actor_email: str,
    dry_run: bool,
) -> ImportReport:
    actor = resolve_actor(
        uow_factory, authorization, organization_id=organization_id, actor_email=actor_email
    )
    try:
        content = read_shelf_workbook(path)
    except WorkbookReadError as error:
        raise ImportRefused(str(error)) from error
    audit = AdministrativeAuditRecorder(clock, uow_factory)
    with uow_factory() as unit_of_work:
        return ImportShelfWorkbookHandler(unit_of_work, clock, audit).handle(
            ImportShelfWorkbookCommand(
                organization_id=organization_id,
                actor_id=actor,
                rows=content.rows,
                headers=content.headers,
                file_sha256=content.file_sha256,
                dry_run=dry_run,
                audit_context=AuditContext(
                    actor_user_id=actor, authorization_organization_id=organization_id
                ),
            )
        )


def format_report(report: ImportReport) -> str:
    if report.dry_run:
        mode = "DRY RUN — nothing written"
    elif report.applied:
        mode = "APPLIED"
    else:
        mode = "NOT APPLIED — fix the rejected rows"
    lines = [
        f"Shelf import: {mode}",
        (
            f"  workbook: {report.places_total} places, {report.sections_total} sections, "
            f"{report.subsections_total} subsections, {report.excluded_total} excluded"
        ),
        (
            f"  created {len(report.created)}, updated {len(report.updated)}, "
            f"unchanged {len(report.unchanged)}, conflicts {len(report.conflicts)}, "
            f"rejected {len(report.rejected)}, missing in workbook "
            f"{len(report.missing_in_workbook)}"
        ),
        (
            f"  sections created {len(report.sections_created)}, renamed "
            f"{len(report.sections_renamed)}; subsections created "
            f"{len(report.subsections_created)}, renamed {len(report.subsections_renamed)}"
        ),
    ]
    if report.ignored_headers:
        lines.append("  ignored columns: " + ", ".join(report.ignored_headers))
    if report.rejected:
        lines.append("Rejected rows:")
        lines.extend(
            f"  row {item.row_number}, «{item.column}» = «{item.value}»: {item.reason}"
            for item in report.rejected
        )
    if report.conflicts:
        lines.append("Conflicts (edited in SafetyMAIN, not applied):")
        for conflict in report.conflicts:
            lines.append(f"  {conflict.code} (row {conflict.row_number})")
            lines.extend(
                f"    {name}: workbook «{diff.workbook}» / SafetyMAIN «{diff.safetymain}»"
                for name, diff in conflict.fields.items()
            )
    if report.missing_in_workbook:
        lines.append("In SafetyMAIN but not in the workbook (left as they are):")
        lines.append("  " + ", ".join(report.missing_in_workbook))
    return "\n".join(lines)


def exit_code(report: ImportReport) -> int:
    return EXIT_REJECTED if report.rejected else EXIT_OK


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import the shelf workbook.")
    parser.add_argument("--organization-id", required=True, type=UUID)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--actor-email", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path, help="Also write the report as JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if not os.environ.get("DATABASE_URL", "").strip():
        print("DATABASE_URL must be set.", file=sys.stderr)
        return EXIT_REFUSED

    from backend.bootstrap.container import create_container
    from backend.bootstrap.settings import load_settings
    from backend.core.infrastructure.time.utc_clock import UtcClock

    container = create_container(load_settings())
    try:
        report = run_import(
            uow_factory=container.uow_factory,
            authorization=container.authorization_service,
            clock=UtcClock(),
            organization_id=OrganizationId(value=args.organization_id),
            path=args.file,
            actor_email=args.actor_email,
            dry_run=args.dry_run,
        )
    except ImportRefused as error:
        print(f"Import refused: {error}", file=sys.stderr)
        return EXIT_REFUSED
    finally:
        container.dispose()
    print(format_report(report))
    if args.report is not None:
        args.report.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
