"""Attach scanned PDFs to shelf places that are «Есть» without a document (TASK-P11-012 §4.5).

For each place that is curated ``present``, has no linked document, names an
active document type without a required approval order, and has a PDF at
``legacy_location`` under ``--root``, the script:

1. creates a draft document (code and title from the place) and links it;
2. sets ``effective_from``;
3. uploads the PDF as the working file;
4. approves and activates the document.

Everything runs through the existing handlers and audit. Source files are only
read: never moved, renamed or deleted. **Dry run by default**; pass ``--apply``
to write. Plan: ``docs/superpowers/plans/2026-11-06-p11-012-attach-shelf-scans.md``.

Usage (backend environment, DATABASE_URL and STORAGE_* set):

    python -m scripts.attach_shelf_scans --organization-id <uuid> --root /path/to/scans \\
        --actor-email curator@example.com [--apply --effective-from 2026-11-06] \\
        [--limit 5] [--report report.json]

Exit codes: 0 done, 1 an applied run had failures, 2 refused.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from uuid import UUID

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
)
from backend.core.application.authorization.authorization_service import (
    AuthorizationService,
)
from backend.core.application.authorization.policies.resource_permissions import (
    COMPLIANCE_DOCUMENT_ACTIVATE,
    COMPLIANCE_DOCUMENT_APPROVE,
    COMPLIANCE_DOCUMENT_CREATE,
    COMPLIANCE_DOCUMENT_UPDATE,
    SHELF_CURATE,
)
from backend.core.application.exceptions.authorization import AuthorizationError
from backend.core.application.handlers.shelf.attach_scan import (
    AttachOutcome,
    AttachShelfScanHandler,
)
from backend.core.application.services.shelf_scan_attachment import (
    LocatedFile,
    LocateResult,
    SkippedPlace,
    SkipReason,
    plan_attachments,
    plan_by_code,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.storage import PresignedUpload, StorageContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.entities.shelf_slot import ShelfSlot
from backend.core.domain.entities.user import UserStatus
from backend.core.domain.exceptions.organization import OrganizationNotFound
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_REFUSED = 2

REQUIRED_PERMISSIONS = (
    SHELF_CURATE,
    COMPLIANCE_DOCUMENT_CREATE,
    COMPLIANCE_DOCUMENT_UPDATE,
    COMPLIANCE_DOCUMENT_APPROVE,
    COMPLIANCE_DOCUMENT_ACTIVATE,
)


class AttachRefused(Exception):
    """The run cannot start; the message is shown to the operator."""


@dataclass
class AttachReport:
    applied: bool
    candidates: list[str] = field(default_factory=list)
    attached: list[AttachOutcome] = field(default_factory=list)
    failed: list[AttachOutcome] = field(default_factory=list)
    skipped: list[SkippedPlace] = field(default_factory=list)


def make_locator(root: Path, max_bytes: int) -> Callable[[str], LocateResult]:
    """Resolve ``legacy_location`` to one PDF strictly inside ``root`` (plan S3)."""
    base = root.resolve()

    def locate(location: str) -> LocateResult:
        relative = location.strip().lstrip("/\\")
        try:
            target = (base / relative).resolve()
        except (OSError, RuntimeError):
            return LocateResult(reason=SkipReason.FILE_NOT_FOUND)
        if target != base and base not in target.parents:
            return LocateResult(reason=SkipReason.OUTSIDE_ROOT)
        if target.is_dir():
            pdfs = sorted(
                item for item in target.iterdir() if item.is_file() and item.suffix.lower() == ".pdf"
            )
            if not pdfs:
                return LocateResult(reason=SkipReason.FILE_NOT_FOUND)
            if len(pdfs) > 1:
                return LocateResult(reason=SkipReason.AMBIGUOUS)
            target = pdfs[0].resolve()
            if base not in target.parents:
                return LocateResult(reason=SkipReason.OUTSIDE_ROOT)
        if not target.is_file():
            return LocateResult(reason=SkipReason.FILE_NOT_FOUND)
        if target.suffix.lower() != ".pdf":
            return LocateResult(reason=SkipReason.NOT_PDF)
        with target.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                return LocateResult(reason=SkipReason.NOT_PDF)
        size = target.stat().st_size
        if size > max_bytes:
            return LocateResult(reason=SkipReason.TOO_LARGE)
        return LocateResult(file=LocatedFile(path=str(target), size_bytes=size))

    return locate


def http_put(presigned: PresignedUpload, data: bytes) -> None:
    """Direct upload to the presigned URL with the signed headers (as the browser does)."""
    request = urllib.request.Request(
        presigned.url, data=data, method=presigned.method, headers=dict(presigned.headers)
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Upload failed with HTTP {response.status}.")


def resolve_actor(
    uow_factory: Callable[[], UnitOfWorkContract],
    authorization: AuthorizationService,
    *,
    organization_id: OrganizationId,
    actor_email: str,
) -> UserId:
    with uow_factory() as unit_of_work:
        try:
            unit_of_work.organizations.get(organization_id)
        except OrganizationNotFound as error:
            raise AttachRefused(f"Organization not found: {organization_id.value}.") from error
        user = unit_of_work.users.get_by_email(actor_email)
    if user is None:
        raise AttachRefused(f"No user with email {actor_email}.")
    if user.status is not UserStatus.ACTIVE:
        raise AttachRefused(f"User {actor_email} is not active.")
    for permission in REQUIRED_PERMISSIONS:
        try:
            authorization.require_permission(
                actor_user_id=user.id, organization_id=organization_id, permission=permission
            )
        except AuthorizationError as error:
            raise AttachRefused(
                f"User {actor_email} lacks {permission.value} in this organization."
            ) from error
    return user.id


def run_attach(
    *,
    uow_factory: Callable[[], UnitOfWorkContract],
    authorization: AuthorizationService,
    clock: ClockContract,
    storage: StorageContract,
    max_upload_bytes: int,
    organization_id: OrganizationId,
    root: Path,
    actor_email: str,
    apply: bool,
    effective_from: date | None,
    limit: int | None = None,
    put: Callable[[PresignedUpload, bytes], None] = http_put,
    match_by_code: bool = False,
    approval_order: str | None = None,
    order_note: str | None = None,
    signed_scan: bool = True,
) -> AttachReport:
    if approval_order and not match_by_code:
        raise AttachRefused("--approval-order needs --match-by-code.")
    if not root.is_dir():
        raise AttachRefused(f"Root is not a directory: {root}.")
    if apply and effective_from is None:
        raise AttachRefused("--effective-from is required with --apply.")
    actor = resolve_actor(
        uow_factory, authorization, organization_id=organization_id, actor_email=actor_email
    )
    with uow_factory() as unit_of_work:
        slots = unit_of_work.shelf_slots.list_all(organization_id)
        types = {item.code: item for item in unit_of_work.document_types.list(organization_id)}
    if match_by_code:
        return _run_signed_editions(
            uow_factory=uow_factory,
            clock=clock,
            storage=storage,
            max_upload_bytes=max_upload_bytes,
            organization_id=organization_id,
            actor=actor,
            slots=slots,
            types=types,
            root=root,
            apply=apply,
            effective_from=effective_from,
            limit=limit,
            put=put,
            approval_order=approval_order,
            order_note=order_note,
            signed_scan=signed_scan,
        )
    plan = plan_attachments(slots, types, make_locator(root, max_upload_bytes))
    candidates = plan.candidates[:limit] if limit else plan.candidates
    report = AttachReport(
        applied=apply,
        candidates=[item.slot.code.value for item in candidates],
        skipped=list(plan.skipped),
    )
    if not apply:
        return report
    assert effective_from is not None
    handler = AttachShelfScanHandler(
        uow_factory,
        clock,
        AdministrativeAuditRecorder(clock, uow_factory),
        storage,
        max_upload_bytes,
        read_bytes=lambda path: Path(path).read_bytes(),
        put=put,
    )
    for candidate in candidates:
        outcome = handler.handle(
            candidate,
            organization_id=organization_id,
            actor_id=actor,
            effective_from=effective_from,
        )
        (report.attached if outcome.attached else report.failed).append(outcome)
    return report


def list_code_files(
    root: Path, max_bytes: int
) -> tuple[list[LocatedFile], list[SkippedPlace]]:
    """PDFs directly in ``root`` (not recursive), checked like ``make_locator``."""
    files: list[LocatedFile] = []
    rejected: list[SkippedPlace] = []
    locate = make_locator(root, max_bytes)
    for entry in sorted(root.iterdir()):
        if not entry.is_file() or entry.suffix.lower() != ".pdf":
            continue
        result = locate(entry.name)
        if result.file is None:
            reason = (result.reason or SkipReason.FILE_NOT_FOUND).value
            rejected.append(SkippedPlace(code="", reason=reason, detail=entry.name))
        else:
            files.append(result.file)
    return files, rejected


def _existing_order_id(
    uow_factory: Callable[[], UnitOfWorkContract],
    organization_id: OrganizationId,
    slot: ShelfSlot,
) -> ComplianceDocumentId | None:
    """On a re-run the order may already be in force on its place."""
    with uow_factory() as unit_of_work:
        documents = unit_of_work.compliance_documents.list_by_ids(
            organization_id, slot.linked_document_ids
        )
    in_force = (ComplianceDocumentStatus.ACTIVE, ComplianceDocumentStatus.UNDER_REVIEW)
    return next((item.id for item in documents if item.status in in_force), None)


def _run_signed_editions(
    *,
    uow_factory: Callable[[], UnitOfWorkContract],
    clock: ClockContract,
    storage: StorageContract,
    max_upload_bytes: int,
    organization_id: OrganizationId,
    actor: UserId,
    slots: Sequence[ShelfSlot],
    types: dict[str, DocumentType],
    root: Path,
    apply: bool,
    effective_from: date | None,
    limit: int | None,
    put: Callable[[PresignedUpload, bytes], None],
    approval_order: str | None,
    order_note: str | None,
    signed_scan: bool,
) -> AttachReport:
    """Signed editions named by place code; the approving order goes first (plan E1–E5)."""
    files, rejected = list_code_files(root, max_upload_bytes)
    plan = plan_by_code(slots, types, files, order_code=approval_order)
    skipped = [*rejected, *plan.skipped]
    order_id: ComplianceDocumentId | None = None
    if approval_order and plan.order is None:
        order_slot = next((slot for slot in slots if slot.code.value == approval_order), None)
        if order_slot is not None and order_slot.linked_document_ids:
            order_id = _existing_order_id(uow_factory, organization_id, order_slot)
            if order_id is not None:
                skipped = [item for item in skipped if item.code != approval_order]
    candidates = list(plan.candidates[:limit] if limit else plan.candidates)
    if approval_order and plan.order is None and order_id is None:
        blocked = [item for item in candidates if item.document_type.requires_approval_order]
        skipped.extend(
            SkippedPlace(code=item.slot.code.value, reason="order_not_in_force") for item in blocked
        )
        candidates = [item for item in candidates if item not in blocked]
    report = AttachReport(
        applied=apply,
        candidates=([plan.order.slot.code.value] if plan.order else [])
        + [item.slot.code.value for item in candidates],
        skipped=skipped,
    )
    if not apply:
        return report
    assert effective_from is not None
    handler = AttachShelfScanHandler(
        uow_factory,
        clock,
        AdministrativeAuditRecorder(clock, uow_factory),
        storage,
        max_upload_bytes,
        read_bytes=lambda path: Path(path).read_bytes(),
        put=put,
    )
    if plan.order is not None:
        outcome = handler.handle(
            plan.order,
            organization_id=organization_id,
            actor_id=actor,
            effective_from=effective_from,
            notes=order_note,
            attach_signed_scan=signed_scan,
        )
        if not outcome.attached:
            # Nothing else is touched when the order cannot be put in force (plan E2).
            report.failed.append(outcome)
            report.skipped.extend(
                SkippedPlace(code=item.slot.code.value, reason="order_failed")
                for item in candidates
            )
            return report
        report.attached.append(outcome)
        assert outcome.document_id is not None
        order_id = ComplianceDocumentId(value=UUID(outcome.document_id))
    for candidate in candidates:
        outcome = handler.handle(
            candidate,
            organization_id=organization_id,
            actor_id=actor,
            effective_from=effective_from,
            approved_by_document_id=(
                order_id if candidate.document_type.requires_approval_order else None
            ),
            attach_signed_scan=signed_scan,
        )
        (report.attached if outcome.attached else report.failed).append(outcome)
    return report


def format_report(report: AttachReport) -> str:
    mode = "APPLIED" if report.applied else "DRY RUN — nothing written"
    lines = [
        f"Shelf scan attachment: {mode}",
        (
            f"  candidates {len(report.candidates)}, attached {len(report.attached)}, "
            f"failed {len(report.failed)}, skipped {len(report.skipped)}"
        ),
    ]
    if not report.applied and report.candidates:
        lines.append("Would attach: " + ", ".join(report.candidates))
    for outcome in report.attached:
        lines.append(f"  attached {outcome.code} → document {outcome.document_id}")
    if report.failed:
        lines.append("Failed (the place keeps its linked document; finish it in the shelf):")
        lines.extend(
            f"  {item.code} at {item.failed_step}: {item.error}" for item in report.failed
        )
    reasons: dict[str, list[str]] = {}
    for item in report.skipped:
        reasons.setdefault(item.reason, []).append(item.code)
    for reason, codes in sorted(reasons.items()):
        shown = [code or "?" for code in codes]
        lines.append(f"  skipped {reason} ({len(codes)}): " + ", ".join(shown))
    for item in report.skipped:
        if not item.code and item.detail:
            lines.append(f"    file «{item.detail}»: {item.reason}")
    return "\n".join(lines)


def exit_code(report: AttachReport) -> int:
    return EXIT_FAILED if report.failed else EXIT_OK


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Attach scanned PDFs to shelf places.")
    parser.add_argument("--organization-id", required=True, type=UUID)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--actor-email", required=True)
    parser.add_argument("--apply", action="store_true", help="Write (default: dry run).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry run (the default; TASK §4.5 spelling). Wins over --apply.",
    )
    parser.add_argument("--effective-from", type=date.fromisoformat)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--match-by-code",
        action="store_true",
        help="Files in --root are named «<place code> <title>.pdf» (signed editions).",
    )
    parser.add_argument(
        "--approval-order",
        help="Place code of the approving order in --root; it is put in force first.",
    )
    parser.add_argument("--order-note", help="Notes for the order, e.g. its number and date.")
    parser.add_argument(
        "--no-signed-scan",
        action="store_true",
        help="Do not also store the PDF as the signed scan (signed editions mode).",
    )
    parser.add_argument("--report", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if not os.environ.get("DATABASE_URL", "").strip():
        print("DATABASE_URL must be set.", file=sys.stderr)
        return EXIT_REFUSED

    from backend.bootstrap.container import create_container
    from backend.bootstrap.settings import load_settings
    from backend.core.infrastructure.time.utc_clock import UtcClock

    settings = load_settings()
    container = create_container(settings)
    try:
        report = run_attach(
            uow_factory=container.uow_factory,
            authorization=container.authorization_service,
            clock=UtcClock(),
            storage=container.storage,
            max_upload_bytes=settings.storage_max_upload_bytes,
            organization_id=OrganizationId(value=args.organization_id),
            root=args.root,
            actor_email=args.actor_email,
            apply=args.apply and not args.dry_run,
            effective_from=args.effective_from,
            limit=args.limit,
            match_by_code=args.match_by_code,
            approval_order=args.approval_order,
            order_note=args.order_note,
            signed_scan=not args.no_signed_scan,
        )
    except AttachRefused as error:
        print(f"Attachment refused: {error}", file=sys.stderr)
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
