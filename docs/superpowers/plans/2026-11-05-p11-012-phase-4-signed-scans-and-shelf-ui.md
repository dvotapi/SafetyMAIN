# TASK-P11-012 Phase 4 (Signed scans and the «Полка» screen) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver acceptance criteria 8–13 of TASK-P11-012 in three parts:

- **Signed scans** (§4.1, P11-001 amendments A2–A4):
  - file role `working | signed_scan` (migration `0016_document_file_role`);
  - a signed scan may be attached to `approved`, `active`, `under_review` documents;
  - `current_file` = the last working file;
  - an inline view URL.
- **The `/shelf` screen** (§4.2–§4.4, §6): overview «Все разделы», the opened bookcase with spines, the place panel with the scan viewer (pdf.js), exclusion (single, bulk, undo), «Разработать», «Загрузить скан», and search. Tokens are «Тёплая бумага».
- **Docs:** ADR-0006 amendment, runbook check, design and API docs.

The optional `scripts/attach_shelf_scans.py` (§4.5) is **not** in this plan. It comes as a separate PR after the user's «да».

**Architecture:**

- *Backend.* Extend the P11-001 file slice:
  - `DocumentFile.role`;
  - a new domain transition `attach_signed_scan`;
  - two signed-scan handlers mirroring `CreateComplianceDocumentUploadUrlHandler` and `ConfirmComplianceDocumentFileHandler`;
  - the `StorageContract.create_download_url` gets a `disposition` argument for the inline view URL.

  The shelf mapper starts filling `signed_scan` and `working_file`. The overview DTO gains `last_imported_at` for the header («реестр сверен … [дата импорта]»).
- *Frontend.* New feature `features/document-shelf/` in the same layout as `features/compliance-documents` (`api/`, `types/`, `schemas/`, `hooks/`, `components/`, `pages/`, `index.ts`). Shared `components/document-viewer/PdfViewer` uses `pdfjs-dist`, pinned and lazily loaded. Rules:
  - every number, status, group, readiness value and action comes from the API (backend-authoritative);
  - dependency-cruiser boundaries hold: the shelf calls compliance endpoints only through its own `api/` module, and reuses `ComplianceDocumentUploadDialog` only through `features/compliance-documents/index.ts` (A5).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic; Next.js 15, React 19, TanStack Query, zod, MSW, Vitest, Playwright + axe, `pdfjs-dist`.

**Spec:** `docs/tasks/TASK-P11-012-document-shelf.md` §4 (4.1–4.4), §6, §7, D1, D7–D10; TASK-P11-001 amendments A2–A5; START prompt «Фаза 4». Where they differ, the TASK wins. The prototype canvas is not accessible to the agent; §4.3 text (sizes, texts) is the reference.

## Delivery split (three PRs, each from fresh `main`)

| PR | Branch | Content | Closes |
|---|---|---|---|
| 4a | `claude/p11-012-phase-4a-signed-scans` | migration 0016, domain role + `attach_signed_scan`, signed-scan endpoints, view URL, versions with `role`, audit, shelf DTO `signed_scan` / `working_file` / `last_imported_at` / new action (Q3), ADR-0006 amendment, API docs | AC 9 (backend part), AC 10 |
| 4b | `claude/p11-012-phase-4b-shelf-overview` | tokens §6, navigation, route `/shelf` + URL state, feature skeleton (API, zod, queries), header + filters, summary, overview strips, opened shelf with spines and tooltips, loading / error / empty states, responsive layout | AC 8 (overview, shelf), part of AC 12 |
| 4c | `claude/p11-012-phase-4c-shelf-panel` | `PdfViewer`, place panel (all branches), actions (develop, confirm, link (Q4), upload scan, upload signed scan), exclusion form (single + bulk, undo), search, A5 export, Playwright + axe | AC 8 (panel), 9 (UI), 11, 12, 13 |

## Global Constraints

- Migration `revision = "0016_document_file_role"`, `down_revision = "0015_document_shelf"`; upgrade and downgrade; literal value list.
- Working files keep D6 (draft only); `approve` / `activate` / `files/current/download-url` keep using the working file; a signed scan never changes those preconditions.
- Signed scans: PDF, JPEG, PNG only; same SHA-256 / size rules (D3, D20); permission `compliance_document:update`.
- The frontend computes nothing (statuses, counts, readiness, actions). The filter chips only dim places by DTO fields, as TASK §4.3 specifies.
- No hex outside `theme/`; new primitives in `primitive.palette`; `shelf-*` semantic tokens reference them; `npm run tokens:build` output committed as the repository already does.
- Accessibility (WCAG 2.2 AA, `docs/design/Accessibility.md`):
  - spines and rows are `<button>`s;
  - tooltips also appear on focus;
  - status is never shown by colour alone;
  - `prefers-reduced-motion` is respected;
  - focus returns to the spine after a panel or form closes.
- `npm run verify` passes on 4b and 4c; backend `pytest` and `-m db` on 4a.
- The real workbook and any real data are never used in tests or screenshots; MSW fixtures are synthetic.

## Decisions taken in this plan (review these)

| # | Decision | Why |
|---|---|---|
| P1 | `DocumentFileRole` enum (`working`, `signed_scan`) in `compliance_enums.py`; `DocumentFile.role` default `working`. Migration 0016 adds `document_files.role VARCHAR(16) NOT NULL DEFAULT 'working'` with CHECK. | §4.1; existing rows become working files. |
| P2 | `ComplianceDocument.current_file` = last file with role `working`; new `current_signed_scan` = last `signed_scan`. `attach_file` refuses a `signed_scan` file. New `attach_signed_scan(file, at, actor_id, expected_version)` is allowed in `approved`, `active`, `under_review`, needs role `signed_scan` and PDF/JPEG/PNG, and bumps the version. | A2/A3; the working-file preconditions are untouched. |
| P3 | Endpoints: `POST /compliance-documents/{id}/signed-scan/upload-url`, `POST …/signed-scan/confirm`, `GET …/files/signed-scan/current/download-url`, `GET …/files/{file_id}/view-url`. Upload and confirm need `compliance_document:update`, download and view need `compliance_document:read`. Bodies mirror the working-file endpoints. A wrong status → 422 `invalid_compliance_document_transition`; no scan → 404 `compliance_document_file_not_found`. | §4.1; mirrors the existing file API. |
| P4 | `StorageContract.create_download_url(..., disposition: Literal["attachment", "inline"] = "attachment")`. Inline uses `inline; filename*=UTF-8''…`. The S3 and in-memory adapters implement it. Callers that do not pass it stay attachment. | A4 with the smallest port change. |
| P5 | Audit `compliance.document.signed_scan_attached`, marked `legacy_identifier=True` like the existing `compliance.document.file_attached` (the action word has an underscore). Registry 76 → 77. See **Q1**. | The TASK name; precedent in the same family. |
| P6 | `files/versions` items gain `role`; the frontend zod schema accepts it. The document object page shows the role label in the versions list. This is a one-line UI change in P11-001, part of A3. | A3 «versions returns role». |
| P7 | Shelf detail DTO: `current_document.signed_scan` = the current signed scan; `working_file` = `current_file`; both carry `file_id`. The panel gets view URLs through the compliance `view-url` endpoint. The overview gains `last_imported_at` = the latest `last_imported_at` of the organization's places (`null` before an import). | §4.3 header line; no frontend calculation. |
| P8 | New shelf action `upload_signed_scan` in `ShelfStatusEvaluator`: a curator-only secondary action when the current in-force document has no signed scan. The evaluator gets the documents' `current_signed_scan`, which it already loads. See **Q3**. | Otherwise there is no place in the UI to attach a signed scan (AC 10), and the frontend must not infer actions. |
| P9 | pdf.js setup: `pdfjs-dist` pinned (exact version), worker loaded lazily from the package (`new URL(…, import.meta.url)`), `disableRange: true`, `disableStream: true`. Each file is fetched with one plain `GET`, which the CORS rules already admit. No runbook change is needed. See **Q2**. | The range and CORS behaviour of MinIO and Yandex cannot be verified locally (the compose MinIO image cannot be pulled, and there is no Yandex access). A plain GET works with the current CORS on both. |
| P10 | Tokens (§6): primitives `paper.50…900`, `graphite.600/400`, `forest.800/500`, `ochre.100…900`, `brick.700/500/100/900`, mapped to the hex values listed in §6. Exact stop names go into `docs/design/Tokens.md`. Semantic `shelf-*` tokens are added for light and dark exactly as the §6 table. A token test checks the contrast pairs (≥ 3:1 graphics, ≥ 4.5:1 spine text). | §6; follows `tokens.json` conventions. |
| P11 | URL state `?section=&slot=&filter=all\|problems\|mandatory&excluded=shown\|hidden`, kept by `use-shelf-url-state` (replace on filter, push on section/slot so back/forward work). Unknown values fall back to defaults. | §4.2. |
| P12 | Data loading: one `GET /shelf` for the header, summary and strips; `GET /shelf/sections/{code}/slots` when a section opens; `GET /shelf/slots/{id}` when a place is selected. Query keys live in `document-shelf/api/shelf-query-keys.ts`. Mutations invalidate the overview, the section and the detail. | §4.3. |
| P13 | Spine sizes, labels, ribbon, ack dot, caret, hover lift, tooltip and ghost are exactly as §4.3.5. The sizes sit in one module `spine-geometry.ts` (a lookup by `document_kind` / `obligation_level`), not calculations. | §4.3. |
| P14 | Panel branches (§4.3.6):<br>- scan block: signed scan first, else the working file labelled «Рабочий файл (без подписи)», else none;<br>- empty states;<br>- details;<br>- actions from `primary_action` / `available_actions` only;<br>- «Исключить с полки» as a danger text button.<br>Layout: right column at ≥ 1200 px, below the shelf at 768–1199 px, a full-screen sheet (Radix Dialog) under 768 px. | §4.3, §4.4. |
| P15 | Exclusion form in the panel, no modal (§4.3.7):<br>- single and bulk use the same component;<br>- the inline error appears when the trimmed comment is under 5 characters, and the backend `comment_too_short` is also mapped to it;<br>- the undo line calls `restore` with the versions returned by the exclude response;<br>- bulk selection mode lives in the URL-independent component state. | §4.3.7, AC 11. |
| P16 | «Разработать»: `POST /develop`. When the place has no type, a type select appears in the panel, fed by the existing `GET /document-types`. Then the browser goes to `/compliance-documents/{id}/edit`. «Загрузить скан» (`present_unverified`): develop, then open the reused upload dialog for the new draft (working file). «Загрузить подписанный скан» (P8): the same dialog with a new prop `target: "working" \| "signed_scan"` that switches it to the signed-scan endpoints. | §4.3.8; A5 export. The dialog prop is a small P11-001 change within A2/A5 (Q3). |
| P17 | «Привязать документ» (`link_document`): an in-panel picker that searches `GET /compliance-documents?search=&subject_kind=organization` and shows code, title and status. Choosing an item posts the link. See **Q4**. | The TASK lists the action but not its UI; this is the smallest option on existing endpoints. |
| P18 | Search in the shelf header (the page's own top bar, not the global shell): a debounced `GET /shelf/slots?q=` combobox (ARIA 1.2 pattern). Choosing a result sets `section` and `slot` in the URL. | §4.3.9; the global shell is a shared component and stays unchanged. |
| P19 | Empty organization (`sections = []`): an invitation «Загрузите реестр-полку» linking to `docs/guides/ShelfImport.md` on the repository host (an external link opened in a new tab). | §4.3.10. |
| P20 | Tests:<br>- 4a: domain, handler, API (status matrix, MIME, permissions, cross-tenant 404, view URL disposition), migration up/down, mapper;<br>- 4b/4c: Vitest + MSW for every component branch, zod schemas, URL state, spine geometry, the token contrast test;<br>- Playwright: section → spine → scan visible → exclude with comment → undo → reload keeps state, plus axe on overview, shelf, panel and form. | TASK §Verification. |

## Implementation notes (4a)

- A signed scan on a wrong status returns 422 `compliance_document_cannot_be_modified`, not `invalid_compliance_document_transition` as P3 said. The status blocks a modification; it is not a lifecycle transition.
- The existing file handlers take a `role` argument (working by default) instead of new handler classes. The signed-scan routes reuse the working-file route functions with the signed-scan handler factories.
- The document response gains `current_signed_scan`, and file items gain `role`. The frontend zod schema accepts `role` with a `working` default and ignores `current_signed_scan`, which only the shelf needs, through its own DTO.
- `upload_signed_scan` is offered only for the in-force statuses (`present`, `review_due`, `overdue_review`, `under_review`), before `exclude`. It is based on the new capability `can_update_document` (`compliance_document:update`).

## Implementation notes (4b)

- «N из M» in the overview row and «N из M в порядке» in the opened shelf show the backend count `by_group.present` of `total`. The page adds nothing up: readiness is the backend percent.
- The overview strip carries only `{code, group}`, so «Обязательные» dims only excluded bars there; the opened shelf dims by `obligation_level`.
- The panel column (≥ 1200 px) is enabled in 4c with the panel; 4b keeps a single column.
- `paper.150` = `#F5F3EC` (spine text) is a primitive stop that §6 uses but did not list.
- Dark «В работе» is `#417760` (4.69:1 spine text, 3.08:1 against the page) instead of the TASK's `#437B62` (4.45:1), as the product owner decided on 2026-11-06; the TASK §6 table is updated.
- Storybook cannot render feature components that import `next/link` (`process is not defined`, existing configuration). Screenshots were taken in the running app with a synthetic workbook imported by the phase 3 script.
- The app shell is wider than a 375 px viewport on every page (pre-existing; not part of this phase).

## Implementation notes (4c)

- `pdfjs-dist` is pinned to **4.10.38**: 5.x requires Node ≥ 22.13, while the production image builds on Node 20.11.
- The bulk request needs `{slot_id, version}`, but `ShelfSlotSummaryDto` had no version (TASK §2.5).
  - First the page read each detail just before the request. The independent review showed that this bypasses optimistic concurrency.
  - `version` was then added to the summary DTO (product owner, 2026-11-06), and the page sends the versions the user saw.
  - Undo restores each place at its freshly read version and reports the places it could not restore.
- Review fixes (PR 4c):
  - the PDF viewer cancels a superseded render;
  - the viewer reloads only when the file changes, not on a new presigned URL;
  - after an upload the whole shelf refreshes;
  - the upload step shows loading and error states;
  - Escape in a field or in the search box does not close the panel;
  - focus moves into an opened form and back to its trigger;
  - action buttons are disabled while a command runs.
- `open_project` links to the linked edition in `draft`/`approved` (from `editions`); `start_review` links to the document page, where the existing lifecycle actions live.
- `ComplianceDocumentUploadDialog` takes `document` as `Pick<…, "id" | "code" | "version">` and the new props `target` and `onUploaded`. The shelf reads `id`, `code` and `version` of the document through its own API module.
- The phone sheet is the panel with fixed full-screen positioning (Escape and the close button close it), not a Radix dialog.
- dependency-cruiser gains `document-shelf-api-no-components` and `document-shelf-presentation-no-fetch`, mirroring the compliance rules.

## Affected files (by PR)

4a — Create: `alembic/versions/0016_document_file_role.py`; tests `tests/domain/test_compliance_document_signed_scan.py`, `tests/api/test_compliance_document_signed_scan_api.py`, `tests/infrastructure/test_document_file_role_migration.py`. Modify:
- domain: `compliance_enums.py`, `compliance_document_components.py`, `compliance_document.py`;
- persistence: document file model, mapper, repository;
- application and API: `handlers/compliance_documents/files.py`, commands, `routers/compliance_documents.py`, schemas, mappers, `operation_ids.py`;
- storage: `contracts/storage.py`, `s3_storage.py`, `in_memory_storage.py`;
- audit: `audit_action.py`, `families/compliance.py`, `tests/core/test_security_event_registry.py`;
- shelf: `shelf_status_evaluator.py` (P8), `handlers/shelf/*` (overview `last_imported_at`), `api/mappers/shelf.py`, `api/schemas/shelf.py`;
- docs: `docs/architecture/ADR-0006-Document-and-Evidence-Storage.md` (amendment), `docs/api/ComplianceDocumentsAPI.md`, `docs/api/ShelfAPI.md`, `docs/architecture/DocumentShelf.md`, the TASK-P11-001 D6 note.

4b — Create:
- `frontend/src/app/shelf/page.tsx`;
- `frontend/src/features/document-shelf/**`;
- `frontend/src/features/document-shelf/*.test.ts(x)`.

Modify:
- `frontend/src/theme/tokens/tokens.json` and the generated theme files;
- `frontend/src/lib/navigation.ts`;
- `docs/design/Tokens.md`, `docs/design/README.md` (shelf pattern);
- `CLAUDE.md` (feature list).

4c — Create:
- `frontend/src/components/document-viewer/**` with tests;
- the panel, exclusion and search components in `features/document-shelf`;
- `frontend/e2e/shelf.spec.ts`.

Modify:
- `frontend/src/features/compliance-documents/index.ts` (A5) and `compliance-document-upload-dialog.tsx` (prop `target`);
- the versions component (role label, P6, if not done in 4a);
- `frontend/package.json` and the lock file (`pdfjs-dist`);
- `.dependency-cruiser.cjs`, only if a rule needs the new shared component listed;
- `docs/design/Accessibility.md` (shelf notes).

## Implementation steps

### PR 4a — Signed scans backend
- [ ] Migration test (role column, default, CHECK; downgrade); migration 0016.
- [ ] Domain tests:
  - `current_file` ignores signed scans;
  - `attach_signed_scan` status matrix and role/MIME rules;
  - `attach_file` refuses a signed scan;
  - approve/activate still need a working file.
- [ ] Domain.
- [ ] Persistence (model, mapper, contract suites with role).
- [ ] Storage `disposition` (adapters and tests: inline header and encoding).
- [ ] Handlers and endpoints (P3), audit (P5), versions `role` (P6).
- [ ] API tests: every status, permission, foreign 404, no-scan 404, MIME, size, SHA mismatch.
- [ ] Shelf: evaluator `upload_signed_scan` (P8), mapper scan fields, overview `last_imported_at` (P7); evaluator and API tests.
- [ ] Docs: ADR-0006 amendment, API docs, P11-001 D6 note.
- [ ] `ruff`, `pytest`, `-m db`, `alembic upgrade/downgrade -1/upgrade`; PR.

### PR 4b — Tokens, route, overview, bookcase
- [ ] Tokens (P10), build, contrast test, `Tokens.md`.
- [ ] Types, zod schemas (all shelf DTOs), API module, query keys, queries; schema tests against fixture payloads.
- [ ] `use-shelf-url-state` (P11), `use-shelf-permissions`; tests.
- [ ] Navigation item, route, page skeleton; loading, error and empty states.
- [ ] Header with filters and the excluded toggle; summary; overview strips (buttons, `aria-expanded`).
- [ ] Opened shelf: sub-shelves, spines (P13), tooltip on hover and focus, legend; dimming by filter; responsive layout.
- [ ] Vitest + MSW tests for each component and state; `npm run verify`; PR.

### PR 4c — Panel, viewer, exclusion, search
- [ ] `PdfViewer` (P9): lazy worker, thumbnails, zoom, keyboard paging, image fallback, «Скачать»; tests with a mocked pdf.js.
- [ ] A5 export and the dialog `target` prop (P16); tests of the existing dialog stay green.
- [ ] Place panel: header, scan block, empty states, details, editions, actions (P14); sheet on phones; focus return.
- [ ] Actions: develop with the type select, confirm applicable, link picker (P17), upload scan, upload signed scan, restore.
- [ ] Exclusion form, single and bulk, with undo (P15).
- [ ] Search combobox (P18).
- [ ] Playwright flow and axe; `npm run verify`; PR with light and dark screenshots of synthetic data.

## Acceptance criteria coverage

| AC | Where |
|---|---|
| 8 | 4b and 4c components; URL round-trip tests; light and dark screenshots |
| 9 | 4a view URL and shelf DTO; 4c `PdfViewer` and the «Рабочий файл (без подписи)» branch |
| 10 | 4a domain and API tests (signed scan on `active`; working file on non-draft still rejected) |
| 11 | 4c exclusion form tests and the Playwright flow; viewer without `shelf:curate` sees exclusion details only |
| 12 | 4b/4c keyboard tests, axe, greyscale check (status by pattern, ribbon and text) |
| 13 | `npm run verify` in 4b/4c; `pytest` + `-m db` in 4a |

## Verification strategy

- Backend: `ruff` on the changed files; `pytest`; `SAFETYMAIN_RUN_DB_TESTS=1 pytest -m db`; migration up/down.
- Frontend: `npm run verify` (tokens → format → lint → typecheck → architecture → test → build); `npm run test:e2e` for the shelf flow against MSW or a local backend with synthetic data.
- Manual: inline rendering against a local backend with `InMemoryStorage` URLs. The real MinIO and Yandex checks wait for Q2.

## Risks

| Risk | Mitigation |
|---|---|
| Inline rendering or CORS on Yandex differs from MinIO | P9 plain GET; Q2 asks for a staging check; fallback «Скачать» always shown |
| `pdfjs-dist` bundle and worker size | Dynamic import only when a PDF is shown; worker as a separate asset |
| 416 spines render slowly | Plain buttons, no per-spine queries; one section rendered at a time |
| Visual drift from the prototype (not accessible to the agent) | §4.3 sizes and texts; screenshots in each PR for the product owner |
| Changing `current_file` semantics breaks P11-001 | Domain and API tests for approve/activate with a signed scan present; existing suites unchanged |

## Known limitations

- `scripts/attach_shelf_scans.py` (§4.5) is not in this plan.
- No acknowledgement block until phase 5.
- Inline rendering on real MinIO and Yandex is not verified by the agent (Q2).

## Open questions

- **Q1.** Is the audit event of the TASK, `compliance.document.signed_scan_attached`, OK as a legacy-format identifier like `compliance.document.file_attached` (P5)? The alternative is a new name in the strict format, `compliance.scan.attached`.
- **Q2.** I cannot check range requests and CORS on MinIO (its image cannot be pulled locally) or on Yandex (no access). Is it OK to configure pdf.js to load the whole file with one plain GET (P9), with no runbook change? Can you check inline viewing on Yandex staging after 4a and 4c?
- **Q3.** Where can users attach a signed scan in the UI? I propose a new backend action `upload_signed_scan` on the place (P8), plus a `target` prop on the reused upload dialog (P16). Alternatively a button on the document page, which would go beyond A2–A5.
- **Q4.** The TASK lists the «Привязать документ» action but not its UI. Is an in-panel search over existing documents (P17) OK?
- **Q5.** Is the split into PRs 4a / 4b / 4c OK, with the optional scan attachment script only after your «да»?
