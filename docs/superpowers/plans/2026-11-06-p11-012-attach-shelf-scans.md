# TASK-P11-012 §4.5 (Optional scan attachment script) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `scripts/attach_shelf_scans.py` closes the gap «Есть, документа в системе нет» in bulk. It takes places that are curated `present`, have no linked document and name a `document_type_code`, and that have a PDF at `legacy_location` under `--root`. For each one it:

1. creates a draft `ComplianceDocument` (code = place code, title = place title);
2. uploads the PDF as the working file;
3. approves and activates it through the existing handlers;
4. links it to the place.

The script never moves, renames or deletes source files. The report lists what was attached and what was skipped, with a reason for each skip. Runs are **dry runs by default**. The product owner gave the go-ahead («да») on 2026-11-06.

**Architecture:** The same layering as the workbook import (phase 3):

- **Planner** (`backend/core/application/services/shelf_scan_attachment.py`) decides per place: candidate or skip with a reason. It is pure, with no file or storage I/O; the script passes in which candidate files exist.
- **Executor** (`AttachShelfScanHandler`, `application/handlers/shelf/attach_scan.py`) runs, per place, the existing handlers in order:
  1. `DevelopShelfSlotDocumentHandler`, which creates the draft and links it in one unit of work;
  2. the upload: `CreateComplianceDocumentUploadUrlHandler` signs a URL, the script PUTs the bytes to it (presigned PUT, as the browser does), then `ConfirmComplianceDocumentFileHandler` attaches the file;
  3. `ApproveComplianceDocumentHandler`;
  4. `ActivateComplianceDocumentHandler`.

  All audit events are recorded as usual, with the curator as the actor.
- **Script:** CLI wiring, actor checks as in the import (active user with `shelf:curate` **and** the document permissions create, update, approve, activate), the PUT over HTTP, the report.

## Decisions taken in this plan (review these)

| # | Decision | Why |
|---|---|---|
| S1 | One place is one sequence of separate transactions: develop+link, upload, confirm, approve, activate. If a later step fails, the place keeps a linked draft (or approved) document and the report says at which step it stopped. Nothing is rolled back or deleted. A re-run skips the place because a document is now linked. The curator finishes it in the UI («Открыть проект»). | The handlers commit separately, and the file PUT goes to storage between them. No DELETE (epic rule). |
| S2 | Skip reasons: `not_present`, `excluded`, `has_document`, `no_document_type`, `type_not_found`, `type_requires_approval_order`, `no_location`, `file_not_found`, `not_pdf`, `outside_root`, `too_large`, plus `failed_at_<step>` for S1. | TASK: «attached / skipped with reason». |
| S3 | `legacy_location` → file: the path is resolved under `--root` and must stay inside it (no `..` or symlink escapes). If it names a **file** ending in `.pdf`, that file is used. If it names a **directory**, it is used only when it holds exactly one PDF (non-recursive); otherwise the skip is `file_not_found` or `ambiguous`. See **Q1**. | The workbook column is free text («Где лежит сейчас (папка 009 …)»), and the TASK assumes it points at a PDF. |
| S4 | Upload: SHA-256 and the size are computed locally; the file is PUT to the presigned URL with the signed headers (`urllib`, no new dependency); then `confirm`. The file is read only. | The same path and checks as the browser (D3, D20). |
| S5 | `effective_from` is required for activation, and the workbook has no reliable date (dates are ignored by design). The script takes `--effective-from YYYY-MM-DD` (required for a real run) and applies it to every attached document. See **Q2**. | Activation refuses a document without it (P11-001). |
| S6 | Types that require an approval order (`requires_approval_order`) are skipped as `type_requires_approval_order`: the script cannot pick the order. | Activation would fail. |
| S7 | Exit codes: 0 done (skips allowed), 1 a real run had at least one `failed_at_*`, 2 refused (actor, organization, root not a directory, missing `--effective-from` on a real run). Optional `--report <json>`; `--limit N` for a trial on a few places. | Same style as the import. |
| S8 | Tests use synthetic files in `tmp_path` and `InMemoryStorage`; the PUT is replaced by a test transport that stores the object. Tests cover every skip reason, a path escaping the root, a full run, a re-run (everything skipped as `has_document`), a dry run that writes nothing, a failure at confirm leaving a linked draft, and the audit events. Plus a `-m db` run. | No real files or storage in tests. |

## Affected files

Create:
- `backend/core/application/services/shelf_scan_attachment.py`;
- `backend/core/application/handlers/shelf/attach_scan.py`;
- `scripts/attach_shelf_scans.py`;
- tests `tests/application/test_shelf_scan_attachment.py`, `tests/infrastructure/test_attach_shelf_scans_script.py`.

Modify:
- `docs/guides/ShelfImport.md` (a «Прикрепление сканов» section);
- `docs/architecture/DocumentShelf.md` (a short note);
- `CLAUDE.md` (the command);
- the TASK status line.

No migration, no API change, no frontend.

## Verification

- `ruff` on the changed files, `pytest`, `-m db`.
- A manual dry run is possible only on your machine with the real folder; the agent will not read it without your instruction.

## Open questions

- **Q1.** What does «Где лежит сейчас» hold in the workbook: a path to a PDF file, a folder, or a description («папка 009, полка 2»)? My proposal (S3): use the value if it is a PDF file or a folder with exactly one PDF, otherwise skip with a reason.
- **Q2.** Which effective-from date should the documents get? My proposal (S5): one date for the whole run through `--effective-from` (for example, the date the scans were checked). Alternatives: take it from the file's modification date, or put the documents in force without the script (only draft + file + approval).
- **Q3.** Is it OK that a place whose run fails halfway keeps a linked draft (S1)? It cannot be deleted (no DELETE), and the curator finishes it in the UI.
