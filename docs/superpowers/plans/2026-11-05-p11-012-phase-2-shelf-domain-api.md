# TASK-P11-012 Phase 2 (Shelf domain, persistence, API) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce the Document Shelf backend: `ShelfSection` (with subsections) and `ShelfSlot` aggregates, the backend-authoritative `ShelfStatusEvaluator` (effective status, groups, readiness, available actions), PostgreSQL persistence (migration `0015_document_shelf`), permissions `shelf:read` / `shelf:curate`, audit events `compliance.place.*` / `compliance.section.*`, and the `/api/v1/shelf` REST API — acceptance criteria 2–5 of TASK-P11-012 (criterion 4's real-data numbers are verified after the phase 3 import).

**Architecture:** Mirror the TASK-P11-001 `DocumentType` / `ComplianceDocument` slice exactly: frozen pydantic entities with `_mutated` transitions and `expected_version`; repository `Protocol`s in `domain/repositories`; in-memory and SQLAlchemy repositories sharing contract suites; handlers built in `backend/api/dependencies.py` and run through `run_audited_admin_operation`; authorization in the router via `require_permission`; tenant isolation through org-scoped repository `get` (foreign → `None` → 404); error codes in `backend/api/error_codes.py`. The evaluator is a pure application service with no I/O; handlers load data and pass `today = clock.now().date()`.

**Tech Stack:** Python 3.12, FastAPI, pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 17, pytest (`-m db`).

**Spec:** `docs/tasks/TASK-P11-012-document-shelf.md` §2 (2.1–2.5), D2, D3, D11, D12; TASK-P11-001 amendment A6. Where they differ from this plan, the TASK wins.

## Delivery split (three PRs, each from fresh `main`)

| PR | Branch | Content | Closes |
|---|---|---|---|
| 2a | `claude/p11-012-phase-2a-shelf-domain` | ids, enums, VOs, `ShelfSection`, `ShelfSlot`, exceptions, `ShelfStatusEvaluator`, repository protocols, in-memory repositories + UoW wiring, contract suites (in-memory run) | AC 2 (domain part), AC 3 (evaluator part) |
| 2b | `claude/p11-012-phase-2b-shelf-persistence` | migration `0015_document_shelf`, SQLAlchemy models / mappers / repositories, SQLAlchemy UoW wiring, contract suites against PostgreSQL, constraint + migration tests | AC 2 (database part) |
| 2c | `claude/p11-012-phase-2c-shelf-api` | permissions, audit registry, handlers (sections + slots + develop), router `/shelf`, schemas, mappers, error codes, API tests, docs | AC 3 (no frontend logic — nothing frontend yet), AC 4 (synthetic data), AC 5 |

Each PR passes the full suite on its own; nothing in 2a/2b is reachable over HTTP until 2c.

## Global Constraints

- Migration `revision = "0015_document_shelf"`, `down_revision = "0014_transport_security_domain"`; upgrade and downgrade; literal value lists inside the migration.
- No physical DELETE in repositories, handlers, or API; no DELETE routes. Unlink is `POST .../unlink`.
- Frontend untouched in phase 2.
- Audit identifiers match `^[a-z]+\.[a-z]+\.[a-z]+$`; no `legacy_identifier=True`.
- Cross-organization access to any shelf resource → 404 (org-scoped `get`).
- P11-001 code changes limited to A6 (extracting the document-building step of the create handler — P12) and to the `_compliance_descriptor` parameter (TASK §2.4). Behaviour of existing endpoints unchanged.
- Code, comments, commits in English. Explicit pathspecs; never stage `.claude/`.

## Decisions taken in this plan (review these)

| # | Decision | Why |
|---|---|---|
| P1 | Files: entities `domain/entities/shelf_section.py`, `shelf_slot.py`; enums `domain/value_objects/shelf_enums.py` (`SlotKeptOn`, `SlotObligationLevel`, `CuratedSlotStatus`, `SlotExclusionReason`, `LegalBasisConfidence`, `ShelfEffectiveStatus`, `ShelfStatusGroup`, `ShelfAction`); VOs `domain/value_objects/shelf_slot_code.py` (`ShelfSlotCode`, with `section_code`, `subsection_code` properties), `shelf_values.py` (`SlotLegalBasis`, `SlotExclusion`); ids `ShelfSectionId`, `ShelfSubsectionId`, `ShelfSlotId` in `safety_ids.py`; exceptions `domain/exceptions/shelf.py`. | Same layout as P11-001. |
| P2 | `ShelfSection` carries `version` and `created_*` / `updated_*` like `ComplianceDocument` (TASK §2.3 lists `version` on `shelf_sections`). Subsections are value objects inside the section aggregate, persisted in `shelf_subsections`; methods `create`, `rename(title)`, `add_subsection(code, title)`, `rename_subsection(code, title)`. Subsection `position` = append order. No removal. | TASK: sections and subsections are only created or renamed. |
| P3 | `document_kind` is validated against a module constant `SHELF_DOCUMENT_KINDS` (the 17 values of TASK §2.1) in `shelf_values.py`, checked in `ShelfSlot` creation/update. "Configurable" = one place to change; no settings/DB table now. | Smallest correct option; no invented storage. |
| P4 | No domain event classes for the shelf. The audit log (`compliance.place.*`) is the record of every change, as for `ComplianceDocument` (P11-001 has none; the existing `safety_events.py` classes have no consumers). See **Q1**. | Avoid dead code; precedent of the nearest slice. Deviates from TASK §2.1 — needs your OK. |
| P5 | `ShelfSlot.link_document` takes the document's `organization_id`, `subject_kind`, `id`, `status`: different organization → `ShelfSlotDocumentNotFound` (404); `subject_kind != organization` → `document_subject_not_supported` (422); already linked → no-op (no version bump, no audit); new document in force (`active`/`under_review`) while another linked document is in force → `already_linked_active_document` (422). Order of `linked_document_ids` = link order. | TASK §2.1, §2.5 error list. Editions: the previous edition is `superseded` by the time the new one becomes active, so at most one linked document is in force. |
| P6 | On an excluded place only `restore` and `update_details` are allowed; `confirm_applicable`, `link`, `unlink`, `develop`, `exclude` → `already_excluded` (422). | Excluded place shows only «Вернуть» (TASK §2.2 actions table). |
| P7 | `develop` precondition: not excluded and no linked document in `draft`, `approved`, `active`, `under_review`; otherwise `already_linked_active_document` (422). Type = request `document_type_code` or the place's; neither → `document_type_required`; unknown or inactive code → `document_type_not_found` (422). See **Q2**. | Prevents duplicate drafts; reuses a TASK error code. |
| P8 | Evaluator lives in `application/services/shelf_status_evaluator.py`, pure: `evaluate(slot, documents, document_types_by_id, today) -> SlotEvaluation(effective_status, group, review_date, current_document_id)`; `available_actions(evaluation, *, can_curate, can_create_document) -> (primary, others)`; `summarize(evaluations) -> counts by group, readiness_percent`. `today` must be a `date` (reject `datetime`, like `is_review_due`). | TASK §2.2: backend-authoritative, fixed-clock unit tests. |
| P8a | (Implementation note, 2a) `open_document` / `start_review` are offered only when the place has a current in-force document, `open_project` only when it has a linked draft/approved document. A curated `present_needs_review` or `in_progress` place without documents therefore gets no primary action (curators still get `link_document` / `exclude` as listed). | The TASK table assumes the document exists; a button without a target would be dead. |
| P9 | Review date: `next_review_at`, else `effective_from + review_period_months` of the document type, else of the place; none → no review rule (status `present`). Threshold = `max(document_type.warning_thresholds_days)`, default 90 when the type is unknown. The divergence from P11-001 D11 (D11 has no place fallback) is documented in `DocumentShelf.md`; P11-001 behaviour unchanged. See **Q3**. | TASK §2.2 first option; aligning both changes P11-001 behaviour. |
| P10 | Current edition = linked in-force document with the latest `effective_from` (ties: latest `updated_at`). `editions[]` = all linked documents, newest `effective_from` first, nulls last. | TASK §2.2 rule 2. |
| P11 | `readiness_percent` = `round_half_up(100 × (present_group + excluded) / total)` as int; `total = 0` → 0. `mandatory_total` = places with `obligation_level = mandatory` (excluded included). `by_group` keys: `present, review, in_progress, missing, to_clarify, excluded`. | D12; integer for display. |
| P12 | `develop` builds the draft through a helper extracted from `CreateComplianceDocumentHandler` (`build_compliance_document(uow, command, now) -> ComplianceDocument`, same module), not by calling `handle()`: `handle()` commits its own unit of work, and the SQLAlchemy UoW commits only once, so nesting would lose the shelf write. The create handler calls the same helper; its behaviour and tests are unchanged. Develop records two audit events in one unit of work: `compliance.document.created` and `compliance.place.linked`. | A6 «through the existing create handler» — same code path, one transaction. |
| P13 | Section handlers (`CreateShelfSection`, `RenameShelfSection`, `AddShelfSubsection`, `RenameShelfSubsection`) exist in the application layer with audit `compliance.section.created` / `updated`, but have **no HTTP endpoints** in phase 2 (TASK §2.5 lists none). Used by tests and by the phase 3 importer. | Smallest API matching the TASK. |
| P14 | Audit registry: `_compliance_descriptor(..., subject_domain=SecurityEventSubjectDomain.COMPLIANCE_DOCUMENT)` keyword with that default; new `SecurityEventSubjectDomain.SHELF = "shelf"` for all place / section / shelf events; `AuditResourceType.SHELF_PLACE = "shelf_place"`, `SHELF_SECTION = "shelf_section"`, `SHELF = "shelf"` (import, phase 3); `AuditAction` members `COMPLIANCE_PLACE_CREATED … UNLINKED`, `COMPLIANCE_SECTION_CREATED / UPDATED`, `COMPLIANCE_SHELF_IMPORTED` (descriptor registered now so the registry is complete; emitted in phase 3). Registry size test 66 → 76. No migration: audit columns are free strings (≤ 64 / ≤ 32). | TASK §2.4; names fit column lengths. |
| P15 | Audit metadata: `slot_id`, `slot_code`, `section_code`, `previous_status` / `new_status` (curated), `expected_version`, `resulting_version`; `excluded` adds `reason`, `comment`; `linked` / `unlinked` add `document_id`, `document_code`; bulk exclude = one event per place. | Same shape as `_meta` in compliance lifecycle. |
| P16 | Permissions: `SHELF_READ`, `SHELF_CURATE` in `SystemPermission`; admin gets both automatically; member and auditor get `SHELF_READ`; constants in `resource_permissions.py`; both added to `_PERMISSION_TO_RESOURCE_TYPE` (`SHELF_PLACE`) and `SHELF_CURATE` to `ADMINISTRATIVE_SYSTEM_PERMISSIONS` (denials audited, like `compliance_document:archive`). | TASK §2.4; `resource_type_for_permission` raises for unmapped permissions. |
| P17 | Link additionally requires `compliance_document:read` (router dependency); develop requires `shelf:curate` + `compliance_document:create`. `available_actions` hides `develop_document` from a curator lacking `compliance_document:create` (impossible today, since only admin curates, but computed honestly). | TASK §2.4, §2.5. |
| P18 | Errors: duplicate place code → 409 `duplicate_shelf_slot_code`; code not matching an existing section/subsection → 422 `shelf_slot_code_mismatch`; unknown `document_type_code` on create/update → 422 `document_type_not_found`; invalid `document_kind` → 422 `shelf_slot_validation_error`; version conflict → 409 `shelf_slot_version_conflict` (bulk: `details.conflicting_slot_ids`); TASK codes `comment_too_short`, `already_excluded`, `not_excluded`, `not_to_clarify`, `document_subject_not_supported`, `document_type_required`, `already_linked_active_document` used verbatim. | TASK §2.5 lists the 422 codes; the rest follow existing naming. |
| P19 | Bulk exclude: 1–200 items, distinct ids; all slots loaded first; any foreign/unknown id → 404 for the whole request; any version mismatch → 409 listing every conflicting id; any already excluded → 422 `already_excluded` listing ids; otherwise all saved and audited in one unit of work. | TASK: all-or-nothing. |
| P20 | Search `GET /shelf/slots?q=&limit=`: case-insensitive substring on `code`, `title`, `short_title`; `limit` default 50, max 100; `q` required, 1–100 chars; results in code order. SQL uses `ILIKE` with escaped `%`, `_`, `\` (P11-001 P5). Excluded places are included (the UI decides display). | TASK §2.5. |
| P21 | Slot code ordering = natural order of `(section.number, subsection position, NN)`; `strip[]` and section lists follow it. | Workbook order. |
| P22 | `excluded_by_name` = user's display name from `uow.users` (empty string if the user no longer exists). | DTO field in TASK §2.5. |
| P23 | `current_document.signed_scan` is always `null` and `working_file` = `current_file` until phase 4; `acknowledgement` = `null`, `has_acknowledgement_gap` = `false` until phase 5. `approved_by_order` resolved from `approved_by_document_id` (same org). | TASK phases 4–5 own those fields. |
| P24 | `import_fingerprint` and `last_imported_at` columns and fields are added now (nullable), never set by phase 2 handlers. | TASK §2.1/§2.3 list them; phase 3 fills them. |

## Approved assumptions

- `shelf:curate` is admin-only until P11-009 (TASK §2.4).
- Sections and subsections are seeded by the phase 3 importer; phase 2 API tests seed them through handlers / repositories.
- AC 4's real numbers (13 sections, `ТрБ` = 14 places in 6 subsections) are checked after the phase 3 import; phase 2 checks counts on synthetic data.

## Backend contract (2c)

Router `backend/api/routers/shelf.py`, prefix `/shelf`, registered in `api/app.py` and the protected prefix list; operation ids in `api/operation_ids.py`.

| Method | Path | Permission | Success |
|---|---|---|---|
| GET | `/shelf` | `shelf:read` | 200 `ShelfOverviewDto` |
| GET | `/shelf/sections/{section_code}/slots` | `shelf:read` | 200 `ShelfSectionSlotsDto`; unknown → 404 |
| GET | `/shelf/slots?q=&limit=` | `shelf:read` | 200 `{items: ShelfSlotSummaryDto[]}` |
| GET | `/shelf/slots/{slot_id}` | `shelf:read` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots` | `shelf:curate` | 201 detail + `Location` |
| PATCH | `/shelf/slots/{slot_id}` | `shelf:curate` | 200 detail (`version` in body) |
| POST | `/shelf/slots/{slot_id}/exclude` | `shelf:curate` | 200 detail |
| POST | `/shelf/slots/{slot_id}/restore` | `shelf:curate` | 200 detail (`{version}`) |
| POST | `/shelf/slots/bulk-exclude` | `shelf:curate` | 200 `{items: ShelfSlotSummaryDto[]}` |
| POST | `/shelf/slots/{slot_id}/confirm-applicable` | `shelf:curate` | 200 detail (`{version}`) |
| POST | `/shelf/slots/{slot_id}/documents` | `shelf:curate` + `compliance_document:read` | 200 detail |
| POST | `/shelf/slots/{slot_id}/documents/{document_id}/unlink` | `shelf:curate` | 200 detail; not linked → 404 |
| POST | `/shelf/slots/{slot_id}/develop` | `shelf:curate` + `compliance_document:create` | 201 `{document_id, slot}` |

DTO shapes exactly as TASK §2.5; `section_code` path parameter is Cyrillic (URL-encoded); request models `extra="forbid"`.

## Architecture boundaries

- `domain/` imports only stdlib, pydantic, domain (architecture tests unchanged).
- Evaluator in `application/services`, no repository access.
- Handlers depend on `UnitOfWorkContract` + `ClockContract` + `AdministrativeAuditRecorder`.
- New repositories: `ShelfSectionRepository` (`add`, `get`, `get_by_code`, `list`, `save(expected_version)`), `ShelfSlotRepository` (`add`, `get`, `get_by_code`, `list_by_section`, `list_all`, `search`, `save(expected_version)`, `list_by_document`); `ComplianceDocumentRepository` gains nothing — linked documents are loaded with `get` per id (≤ a few per place) and, for the overview, one `list_by_ids(org, ids)` addition. See **Q4**.

## Affected files

2a — Create: `domain/entities/shelf_section.py`, `shelf_slot.py`; `domain/value_objects/shelf_enums.py`, `shelf_slot_code.py`, `shelf_values.py`; `domain/exceptions/shelf.py`; `domain/repositories/shelf_section_repository.py`, `shelf_slot_repository.py`; `application/services/shelf_status_evaluator.py`; `infrastructure/persistence/in_memory/shelf_section_repository.py`, `shelf_slot_repository.py`; tests `tests/domain/test_shelf_slot_code.py`, `test_shelf_section.py`, `test_shelf_slot.py`, `tests/application/test_shelf_status_evaluator.py`, `tests/contracts/test_shelf_section_repository_contracts.py`, `test_shelf_slot_repository_contracts.py`, `tests/fixtures/shelf.py`. Modify: `safety_ids.py`, `domain/repositories/__init__.py`, `in_memory/unit_of_work.py`, `in_memory/__init__.py`. Create `tests/core/test_shelf_in_memory_unit_of_work.py`. (Implementation note: `contracts/unit_of_work.py` moves to 2b together with `SQLAlchemyUnitOfWork`, so the contract never declares repositories that one implementation lacks; nothing uses `uow.shelf_*` before 2c.)

2b — Modify: `contracts/unit_of_work.py` (shelf repositories). Create: `alembic/versions/0015_document_shelf.py`; `sqlalchemy/models/shelf_*_model.py`; `sqlalchemy/mappers/shelf_*_mapper.py`; `sqlalchemy/repositories/shelf_*_repository.py`; tests `tests/infrastructure/test_document_shelf_migration.py`, `test_shelf_constraints.py`, `tests/contracts/test_sqlalchemy_shelf_*_contracts.py`. Modify: `sqlalchemy/unit_of_work.py`, `models/__init__.py`, `repositories/__init__.py`, `test_transport_security_domain_migration.py` (only if it pins head — it pins its own revision, unchanged).

2c — Create: `application/commands/shelf.py`, `application/queries/shelf.py`, `application/handlers/shelf/*.py`, `api/routers/shelf.py`, `api/schemas/shelf.py`, `api/mappers/shelf.py`; tests `tests/api/test_shelf_api.py`, `test_shelf_commands_api.py`, `test_shelf_develop_api.py`, `tests/core/test_shelf_handlers_audit.py`; docs `docs/api/ShelfAPI.md`, `docs/architecture/DocumentShelf.md`, `docs/domain/ShelfSlot.md`. Modify: `permission.py`, `role_permissions.py`, `resource_permissions.py`, `permission_denial_audit.py`, `families/compliance.py`, `subject_domains.py`, `audit_resource_type.py`, `audit_action.py`, `failure_codes.py`, `error_codes.py`, `api/dependencies.py`, `api/app.py`, `api/operation_ids.py`, `create_compliance_document.py` (P12), `tests/core/test_security_event_registry.py` (66 → 76), `docs/architecture/AuditTaxonomy.md`, `docs/domain/UbiquitousLanguage.md`, `docs/api/ComplianceDocumentsAPI.md` (develop link note), `CLAUDE.md` / `AI_CONTEXT.md` (aggregates, router).

## Implementation steps

### PR 2a — Domain and evaluator
- [ ] `ShelfSlotCode` VO tests (valid `ТрБ.02.02`, `ПожБ.01.10`; reject `ТрБ.2.02`, Latin, missing parts; `section_code`, `subsection_code`) → implement.
- [ ] `ShelfSection` tests (code regex `^[А-ЯЁа-яё]{2,6}$`, number 1–99, subsection code `SECTION.SS` and uniqueness, rename, version) → implement.
- [ ] `ShelfSlot` tests: create validates code prefix/subsection against the section (AC 2), field limits, `applicability_condition` required when conditional, `document_kind` vocabulary, `exclude` (comment trim ≥ 5, ≤ 1000, stores `status_before`), `restore`, `confirm_applicable`, `link_document` (P5), `unlink_document`, P6, version checks → implement.
- [ ] Evaluator tests with fixed `today` for every rule of §2.2 in order, every curated fallback, review-date fallbacks (P9), threshold default, current-edition choice (P10), groups, readiness (P11), action table incl. non-curator view (P17) → implement.
- [ ] Repository protocols, in-memory repositories (code uniqueness incl. excluded; version conflict), contract suites, UoW wiring (snapshot/rollback).
- [ ] `ruff` (changed files), `pytest`.

### PR 2b — Persistence
- [ ] Migration test (module; `-m db` schema: tables, uniques, CHECKs incl. exclusion all-or-none and comment length, FKs, indexes; downgrade to 0014 and back).
- [ ] Migration `0015` per TASK §2.3.
- [ ] Models, mappers, repositories (`UPDATE ... WHERE version`; IntegrityError on `uq_shelf_slots_organization_id_code` → `DuplicateShelfSlotCode`; link table rewritten on save by diff — insert new, update nothing, remove unlinked rows (row removal in the link table is the unlink itself, audited; see **Q5**)).
- [ ] SQLAlchemy contract runs, constraint tests, restart persistence test.
- [ ] `alembic upgrade head / downgrade -1 / upgrade head`; `pytest -m db`.

### PR 2c — Application, RBAC, audit, API, docs
- [ ] Permissions + tests (member/auditor read only, admin both).
- [ ] Audit registry changes + registry tests.
- [ ] P12 refactor of the create handler (existing tests green before continuing).
- [ ] Handlers + audit tests (success and failure specs).
- [ ] Router, schemas, mappers, error codes; API tests: RBAC 403, foreign 404, 409, every 422 code, bulk atomicity, develop atomic (document + link + two audit events), overview counts = evaluator.
- [ ] Docs listed above; `DocumentShelf.md` records P9 divergence.
- [ ] Full verification, self-review, PR.

## Acceptance Criteria coverage

| AC | Where |
|---|---|
| 2 | 2a domain tests (mismatch), 2a contract + 2b DB unique (duplicates incl. excluded), 2c API 409/422 |
| 3 | 2a evaluator unit tests with fixed date; no frontend in this phase |
| 4 | 2c API test on a synthetic 2-section shelf; real numbers after phase 3 |
| 5 | 2c API tests per command: preconditions, 409, 403, 404, audit, bulk all-or-nothing |

## Verification strategy

- `python -m ruff check <changed files>` (full `ruff check .` has 410 pre-existing findings with ruff 0.16.3).
- `python -m pytest`; `SAFETYMAIN_RUN_DB_TESTS=1 python -m pytest -m db` (2b, 2c).
- `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` (2b).
- Architecture tests and security event registry tests unchanged except the size constant.

## Risks

| Risk | Mitigation |
|---|---|
| Overview over ~416 places loads all slots and their documents per request | One `list_all` + one documents-by-ids query + one types query; evaluator in memory. Acceptable at this size; measure in 2c API test with 500 synthetic places. |
| Cyrillic section codes in URL paths | API test with URL-encoded `ТрБ` / `ПожБ`. |
| `ILIKE` Cyrillic folding needs UTF-8 ctype | Same check as P11-001 (passes on compose/CI). |
| Refactor of the create handler (P12) | Pure extraction; existing compliance API tests must stay green unchanged. |

## Known limitations

- No HTTP endpoints for sections (P13); renaming sections needs re-import or a later task.
- No domain event classes (P4, pending Q1).
- Signed scan, view URL, acknowledgement fields are placeholders until phases 4–5.

## Open questions

- **Q1.** TASK §2.1 lists domain events (`ShelfSlotCreated`…). The nearest slice (ComplianceDocument) has none, and the existing safety events have no consumer. OK to skip them (P4) and rely on audit events?
- **Q2.** `develop` when a draft/approved document is already linked: reject with `already_linked_active_document` (P7), or allow a second draft?
- **Q3.** Review-due divergence: keep the shelf fallback to the place's `review_period_months` and document the divergence (P9, recommended), or align P11-001 D11 to the same rule (changes the documents registry)?
- **Q4.** Adding `list_by_ids(organization_id, ids)` to `ComplianceDocumentRepository` (in-memory + SQLAlchemy) — a small P11-001 extension outside A1–A6. OK?
- **Q5.** Unlinking deletes the row from the link table `shelf_slot_documents` (the documents themselves are never deleted; the unlink is audited). TASK forbids physical DELETE of places, sections, and documents — is a link-row delete acceptable, or should links be soft (`unlinked_at`)?
