# TASK-P11-012 Phase 3 (Workbook import) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import the curated workbook «Полка документов» into the shelf.

- `scripts/import_shelf_workbook.py` reads sheet «Полка» by header names and maps every column (§3.2).
- It generates short titles (§3.3).
- It creates or updates sections, subsections and places idempotently, never overwriting places edited in SafetyMAIN (D3, §3.4).
- It reports created / updated / unchanged / conflicts / rejected / missing-in-workbook, and supports `--dry-run`.
- A real run emits one `compliance.shelf.imported`.
- Curator guide `docs/guides/ShelfImport.md`.

This closes acceptance criteria 6–7 and the real-data part of criterion 4.

**Architecture:** Three layers, the same split as the rest of the slice:

1. **Reader** (`backend/core/infrastructure/importing/shelf_workbook_reader.py`, `openpyxl`). The only code that touches the file. It returns `WorkbookRow(row_number, values: dict[header, str])`. The application never imports `openpyxl`.
2. **Mapping** (`backend/core/application/services/shelf_import_mapping.py`). Pure functions with no I/O:
   - map one row to `MappedPlace` (place fields, section number and title, subsection title, safety domain) or to a list of row errors;
   - generate the short title (§3.3);
   - compute the fingerprint (§3.4).
3. **Handler** `ImportShelfWorkbookHandler` (`backend/core/application/handlers/shelf/import_workbook.py`). It compares mapped rows with what is stored and builds an `ImportPlan`. A real run applies the plan in **one unit of work**, through the same domain transitions and audit specs as the API (`compliance.section.*`, `compliance.place.*`), plus one `compliance.shelf.imported`. A dry run builds the same plan and writes nothing.

The script only wires these together: it resolves the actor, runs reader → handler and prints the report.

**Tech Stack:** Python 3.12, `openpyxl` (new optional extra `import`, also in `dev`), SQLAlchemy 2, pytest (`-m db`).

**Spec:** `docs/tasks/TASK-P11-012-document-shelf.md` §3 (3.1–3.5), D3, D11, §7 (guide); START prompt «Фаза 3». Where they differ, the TASK wins.

## Global Constraints

- No migration: `import_fingerprint` and `last_imported_at` already exist (0015).
- Tests use only synthetic workbooks generated in the test (`openpyxl` in `tmp_path`). The real workbook is never copied into the repository, read by tests, or attached.
- The repository is **public**: the PR shows only the dry-run **counts** of the real workbook, never codes, titles or notes.
- No DELETE: places missing from the workbook are reported, never excluded or removed.
- Unknown vocabulary values are rejected with row number, column and value; never guessed.
- Audit identifiers already registered in 2c; no new `AuditAction`.
- Code, comments, commits in English; explicit pathspecs; never stage `.claude/`, `scripts/pilot/`, or the P11-001 plan file.

## Decisions taken in this plan (review these)

| # | Decision | Why |
|---|---|---|
| P1 | Layout: reader in `infrastructure/importing/`, mapping in `application/services/shelf_import_mapping.py`, handler in `application/handlers/shelf/import_workbook.py`, CLI `scripts/import_shelf_workbook.py` with `main(argv)` and a testable `run_import(session_factory, …) -> ImportReport`. | Architecture tests forbid `openpyxl` in application/domain; the `seed_document_types` precedent makes the script testable without a subprocess. |
| P2 | Header row = the first row in the first 10 that contains all required headers. Headers are matched after normalisation: trim, collapse whitespace, `ё`→`е`, case-insensitive. Required headers: Код, Раздел, Подраздел, Документ (место на полке), Вид, Ведётся на, Обязательность, Статус. A missing required header aborts with the list of missing names. The other §3.2 headers are optional (empty when absent). | TASK: by names, not by index; the real header row is 3, but synthetic tests and future layouts may differ. |
| P3 | Value normalisation before mapping: trim, collapse internal whitespace, unify dashes (`—`, `–`, `-` with surrounding spaces) for vocabulary lookups, compare case-insensitively. Empty cells and `—` mean «empty». Numbers in «Период, мес» accept `36`, `36.0`, `«36»`; anything else is rejected. | Spreadsheet cells mix floats, dashes and stray spaces; strict but not brittle. |
| P4 | Vocabularies exactly as §3.2, with the «Обязательна» variant: kept_on (6 values), obligation (4 spellings → 3 values), status (6 values incl. «Не применимо»), confidence rules incl. the free-text rule (original text appended to `notes` as `Достоверность: <text>`). «Вид» is validated against the domain list `SHELF_DOCUMENT_KINDS`; the sheet «Справочники» is not read. See **Q4**. | One source of truth for the vocabulary in code. |
| P5 | «Домен SafetyMAIN»: the column holds codes of `SafetyDomain` (and the legacy `labour`, mapped to `transport_security`). All rows of a section must agree, otherwise every row of that section is rejected with the conflicting values. | §3.2. |
| P6 | «Тип в SafetyMAIN»: a value that is an existing **active** `DocumentType.code` of the organization → `document_type_code`; anything else (`(новый)`, `журнал (P11-005)`, free text) → `proposed_document_type`, `document_type_code = null`. | §3.2. |
| P7 | Section: number and title from «Раздел» by `^(\d{1,2})\s+(.+)$`; section code = prefix of `Код`. Every row of a section must give the same number and title, otherwise rejected. Subsection code = first two parts of `Код`, title = «Подраздел»; the same agreement rule. | §3.2; a section/subsection is defined by many rows. |
| P8 | Short title (§3.3), deterministic: drop parenthesised fragments; apply the abbreviation list in the given order, case-insensitive on whole words; collapse whitespace; if longer than 40, cut at the last word boundary ≤ 39 and append «…» (hard cut when there is none). The list lives as a tuple of pairs next to the function. | §3.3; deterministic so the fingerprint is stable. |
| P9 | Fingerprint = SHA-256 (hex) of the JSON (sorted keys, UTF-8, no whitespace) of the **mapped place values**: every place field the workbook sets, plus the import status (`curated_status`, or `excluded`). The short title is the generated one. Sections are not part of it. | §3.4 «normalised mapped values of the row». |
| P10 | **Conflict detection** (see **Q1**): a stored place counts as edited in SafetyMAIN when the fingerprint of its **current** mapped values (same function, computed from the stored place) differs from its stored `import_fingerprint`. Row unchanged = row fingerprint equals stored fingerprint → `unchanged` (also when the place was edited in SafetyMAIN). Row changed and place not edited → `updated`. Row changed and place edited → `conflict` with field-level differences (workbook vs SafetyMAIN), not applied. A place created in SafetyMAIN (no fingerprint) whose code appears in the workbook → conflict. | Field-level and actor-independent: linking a document or the curator being the import actor do not create false conflicts. The TASK wording («`updated_at` later than `last_imported_at` by a non-import actor») cannot tell the import from the same curator editing in the UI. |
| P11 | Exclusion from the workbook: «Не применимо» on a new place → `create` then `exclude(not_applicable, «Статус «Не применимо» из реестра-полки»)`, `status_before = to_clarify` (curated status is created as `to_clarify`). On an existing, not-edited place: becoming «Не применимо» → exclude; leaving «Не применимо» → restore, then set the mapped curated status. | §3.2; uses the same domain transitions and audit events as the API. |
| P12 | A real run is **all-or-nothing**: any rejected row (or section disagreement) → nothing is written, exit code 1, the report lists the rejections. Conflicts do not block the run (they are reported and skipped). A dry run with rejections also exits 1. See **Q2**. | One consistent state of the shelf; matches «zero rejected rows» before a real run. |
| P13 | One unit of work per real run. Section and subsection creation and renames use the existing section handlers' domain methods and `compliance.section.*` specs; places use `ShelfSlot.create` / new `ShelfSlot.apply_import` and `compliance.place.created` / `updated` / `excluded` / `restored` specs. A real run records `compliance.shelf.imported` (resource `SHELF`) with counts and `file_sha256`. If nothing changes, the import is still recorded, with zero counts. | §3.1 «through application handlers, same audit as the API»; one event per non-dry run (AC 6). |
| P14 | Domain additions in `ShelfSlot`: `create(..., import_fingerprint=None, imported_at=None)` and `apply_import(*, values, fingerprint, at, actor_id, expected_version)`. `apply_import` sets the mapped fields, `import_fingerprint` and `last_imported_at` in one version bump. It may change only mapped fields, never code, section, links or an exclusion. Excluding and restoring stay separate transitions (P11). `update_details` still refuses the import fields. | The import fields must not be editable through the API (D3 integrity). |
| P15 | Section renames: if the workbook gives a different section or subsection title than stored, the import renames it (audited `compliance.section.updated`). Sections have no SafetyMAIN edit path yet (2c P13), so no conflict is possible. A section whose number differs → rejected (number is unique and drives order). See **Q3**. | Keeps the catalogue in sync without inventing section conflict tracking. |
| P16 | Actor: `--actor-email` → `uow.users.get_by_email`. The user must be active and hold `shelf:curate` in the organization, checked with the container's `AuthorizationService`. Otherwise the script exits 2 before reading the file. The organization must exist. | Same audit actor as the API; no import as a non-curator. |
| P17 | Report: `ImportReport` with counts and items: rejected rows (`row`, `column`, `value`, `reason`), conflicts (`code`, `fields: {name: {workbook, safetymain}}`), missing-in-workbook codes, plus sections and subsections created and renamed. Human-readable output to stdout (counts first). Optional `--report <path.json>`. The report never prints quotes or notes in full: values are cut to 80 characters. | §3.4; the report may be pasted into issues. |
| P18 | Audit metadata keys added to `ALLOWED_METADATA_KEYS`: `created_count`, `updated_count`, `unchanged_count`, `conflict_count`, `rejected_count`, `missing_count`; `file_sha256` already exists. | `compliance.shelf.imported` payload = counts + source SHA-256 (§2.4). |
| P19 | `openpyxl` opened with `read_only=True, data_only=True` (cached formula values). The script refuses a non-`.xlsx` file and a file over 20 MB. | Formulas in the workbook (e.g. «Дней до пересмотра») are ignored anyway; bounded input. |
| P20 | Ignored columns: «Дата утверждения / выдачи», «Следующий пересмотр», «Дней до пересмотра», and any header not in §3.2 (listed once in the report as «ignored columns»). | §3.2. |

## Implementation notes

- «Домен SafetyMAIN» is a required header too: every section needs a domain (P5).
- A file header may add a note in parentheses after a known name: the real workbook has «Где лежит сейчас (папка 009 …)».
- The production backend image does not install the `import` extra. The guide explains running the import from an operator machine with the production `DATABASE_URL`. The Dockerfile is unchanged.
- Real workbook dry run (read in place, local database, throwaway organization):
  - 416 rows: 415 mapped, 1 rejected, a «Вид» value missing from the vocabulary, a workbook fix;
  - 13 sections, 92 subsections, 3 excluded; `ТрБ` = 14 places in 6 subsections;
  - an in-memory import of the 415 valid rows followed by a re-run reports 415 unchanged and 0 conflicts.

## Affected files

Create:
- `backend/core/infrastructure/importing/__init__.py`, `shelf_workbook_reader.py`
- `backend/core/application/services/shelf_import_mapping.py`
- `backend/core/application/handlers/shelf/import_workbook.py` (+ export in `handlers/shelf/__init__.py`)
- `backend/core/application/commands/shelf.py`: `ImportShelfWorkbookCommand` (organization, actor, rows, `file_sha256`, `dry_run`)
- `scripts/import_shelf_workbook.py`
- tests:
  - `tests/fixtures/shelf_workbook.py` (synthetic workbook builder);
  - `tests/application/test_shelf_import_mapping.py`, `tests/application/test_shelf_short_title.py`;
  - `tests/infrastructure/test_shelf_workbook_reader.py`;
  - `tests/core/test_shelf_import_handler.py`;
  - `tests/scripts/test_import_shelf_workbook.py` (in-memory and `-m db`).
- `docs/guides/ShelfImport.md` (new folder)

Modify:
- `backend/core/domain/entities/shelf_slot.py`: P14
- `backend/core/domain/entities/audit_event.py`: P18
- `pyproject.toml`: extra `import = ["openpyxl>=3.1"]`, `openpyxl` in `dev`
- `docs/architecture/DocumentShelf.md`: import contract, P10
- `docs/api/ShelfAPI.md`: a sentence on imported fields
- `CLAUDE.md`: command; `docs/tasks/TASK-P11-012-document-shelf.md`: status line

## Implementation steps

- [ ] Synthetic workbook builder (`tests/fixtures/shelf_workbook.py`): header row at row 3 with title rows above, every §3.2 column, helpers to add rows.
- [ ] Reader tests: header detection by name at any of the first 10 rows, missing required header, ignored columns, cell types (float, int, None, «—»).
- [ ] Implement the reader.
- [ ] Mapping tests:
  - every vocabulary mapping and the «Обязательна» spelling;
  - confidence rules incl. free text → notes;
  - `labour` → `transport_security` and a section with mixed domains → rejected;
  - conditional without condition → rejected;
  - unknown values → rejected with row and column;
  - «Раздел» parsing;
  - type code vs proposed text.
- [ ] Implement the mapping.
- [ ] Short title tests: abbreviations, parentheses, ≤ 40 characters, word-boundary cut, determinism.
- [ ] Implement the short title.
- [ ] Domain tests for `apply_import` and `create` with import fields (P14), and for `update_details` still refusing them.
- [ ] Implement the domain additions.
- [ ] Handler tests (in-memory UoW, fixed clock):
  - first run creates sections, subsections and places, including exclusions;
  - second run → all unchanged, one more `compliance.shelf.imported`;
  - changed row on an untouched place → updated;
  - changed row on a place edited in SafetyMAIN → conflict, not applied (AC 7);
  - linking a document is not a conflict;
  - missing-in-workbook reported, not excluded;
  - rejected row → nothing written;
  - dry run writes nothing and records nothing;
  - audit events and counts.
- [ ] Implement the handler.
- [ ] Script tests:
  - actor checks (unknown, inactive, non-curator → exit 2);
  - `--dry-run`, `--report` JSON;
  - exit codes;
  - `-m db` run against PostgreSQL, twice (idempotency).
- [ ] Implement the script; add the extras to `pyproject.toml`.
- [ ] Guide `docs/guides/ShelfImport.md`: preparing the workbook, dry-run, reading the report, resolving conflicts, reviewing short titles per section. Other docs as listed.
- [ ] Verification:
  - `ruff` on the changed files, `pytest`, `-m db`;
  - after approval (Q5), a dry run on the real workbook, read in place; post counts only.
- [ ] Self-review, PR.

## Acceptance criteria coverage

| AC | Where |
|---|---|
| 4 (real numbers) | After the user's real run: `GET /shelf` → 13 sections; `ТрБ` → 14 places in 6 subsections. Checked on the real dry-run report counts per section. |
| 6 | Dry-run report on the real workbook (counts only in the PR); handler test: real run creates, second run reports all unchanged; one `compliance.shelf.imported` per real run. |
| 7 | Handler test: place edited in SafetyMAIN + changed row → conflict, place unchanged. |

## Verification strategy

- `python -m ruff check <changed files>`.
- `python -m pytest`; `SAFETYMAIN_RUN_DB_TESTS=1 python -m pytest -m db`.
- Architecture tests: `openpyxl` only in `infrastructure/importing` and `scripts/`.
- Manual (after Q5): `python scripts/import_shelf_workbook.py --organization-id <test org> --file <real path> --actor-email <curator> --dry-run`, run against the local compose database with a test organization. The file is read in place.

## Risks

| Risk | Mitigation |
|---|---|
| Real headers or vocabularies differ from §3.2 | Strict rejection with row/column/value; dry-run first; the guide explains fixes. |
| Short titles poor | Deterministic, editable; the guide recommends a review per section; editing counts as a SafetyMAIN edit (P10). |
| Fingerprint changes when the mapping code changes (e.g. new abbreviation) | Every place would show as «updated» on the next run (or conflict if edited). Documented in the guide; the abbreviation list changes only with a plan. |
| Large single transaction | ~416 places × a few statements; acceptable. |
| Cached formula values missing when the file was saved by a tool that does not store them | Only ignored columns hold formulas. |

## Known limitations

- The sheet «Справочники» is not read (P4).
- Sections are renamed from the workbook without conflict tracking (P15).
- No scheduled or UI import; CLI only.

## Open questions

- **Q1.** Conflict detection by comparing the current place values with the fingerprint stored at the last import (P10) instead of the TASK's «`updated_at` later than `last_imported_at` by a non-import actor». This catches any edit to an imported field and ignores linking documents. OK?
- **Q2.** Is a real run all-or-nothing when any row is rejected (P12, recommended), or should it import the valid rows and skip the rejected ones?
- **Q3.** Is it OK to rename sections and subsections from the workbook without conflict checks (P15)? There is no way to edit them in SafetyMAIN yet.
- **Q4.** Should «Вид» be validated only against the list in code, without reading the sheet «Справочники» (P4)? If the sheet has a value that is not in the list, the row is rejected, and adding the value is a code change.
- **Q5.** May I read the real workbook in place (read-only, never copied) for the final dry run against the local database, and post only the counts in the public PR? Or will you run the dry run yourself?
