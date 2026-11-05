# TASK-P11-012 — Document Shelf ("Полка")

Status: **Approved** — Phase 1 specification approved by the product owner on 2026-11-05. Phase 1 (transport security domain) implemented; plan `docs/superpowers/plans/2026-11-05-p11-012-phase-1-transport-security.md`. Next: Phase 2 planning per `docs/ai/DevelopmentWorkflow.md` (investigation only, no code until the plan is approved).
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-001 (Done) for phases 1–4; for phase 5: TASK-P11-004 (and its worker prerequisite), TASK-P11-005 (acknowledgement journal only), the `acknowledge_document` slice of TASK-P11-006, and the position codes of D5
Related: TASK-P11-009 §8 (requirements link to shelf places; seed from places; excluded places → `not_applicable`; `compliance_curator` gets `shelf:*`), TASK-P11-008 §6 (coverage for places kept on employees), TASK-P11-010 (impact analysis includes places), TASK-P11-001 «Amendments after completion» (A1–A6)
Prototype: claude.ai canvas «Полка — SafetyMAIN» (interactive, built on the real workbook; private to the product owner): https://claude.ai/artifact/GKpQWcEPC4gpXSzJT31pFe

---

## Goal

Give the organisation one screen that answers three questions:

1. Which instructions, regulations, orders, programmes, journals, and other documents must we have?
2. Which of them do we have, in which state, and with a signed scan?
3. Is everyone who must know a document by the nature of their work acquainted with its current edition?

The screen is a bookcase: an overview strip per section of the safety system, and an opened shelf where every **place** is a spine. A place exists even when its document does not — an empty place is the most important thing on the page. Clicking a spine opens the place panel with the signed scan, lifecycle data, legal basis, and acknowledgement coverage. Curators can exclude places that do not apply, singly or in bulk, with a reason.

The initial content is imported from the curated workbook `Полка документов ОТ и ПБ.xlsx` (version 2, reconciled with legislation on 2026-10-23): 416 places in 13 sections.

---

## Context

### The workbook (source of the initial data)

Maintained by the occupational-safety specialist and the product owner; lives outside the repository (internal data — never commit it).

- Sheet «Полка», header in row 3, data from row 4; 26 columns (mapping in §4.2).
- Codes are permanent: `SECTION.SS.NN`, e.g. `ВМ.10.01` = section «Взрывчатые материалы и БВР», subsection 10, place 1. New places are appended to the end of a subsection; places that do not apply get «Не применимо» and are never deleted. Verified on 2026-11-04: all 416 codes match `^[А-ЯЁа-яё]+\.\d{2}\.\d{2}$`, no duplicates, every «При условии» row has a condition.
- 13 sections with prefixes `СУ, ОТ, ЭБ, ПБ, ВМ, ГР, ПС, ПожБ, БДД, ТрБ, ДОПОГ, ООС, ГОЧС` (mixed case: `ПожБ`), 92 subsections.
- Status distribution: Нет 159, Уточнить 159, Есть 49, В работе (проект) 44, Не применимо 3, Есть — нужен пересмотр 2.
- «Ведётся на»: Организация 177, ОПО / объект 62, Событие 49, Работник 53, ТС / техника 40, Профессия / вид работ 35.
- «Обязательность»: Обязателен 244 (+1 spelled «Обязательна»), При условии 160, Рекомендуется 11.
- Other sheets («Сводка», «План разработки», «Оформить и проверить», «Изменения НПА», «Структура папок») are out of scope.

### What exists in the codebase

- `ComplianceDocument` (P11-001): lifecycle `draft → approved → active ↔ under_review → superseded`, archive/restore; `next_review_at`, `effective_from`, `applicability` (free-text positions / work types / departments, `asset_ids`); files in object storage via presigned URLs (`/compliance-documents/{id}/files/upload-url | confirm | current/download-url | versions`). Decision D6: files attach only in `draft`; `approve` requires a current file. The download URL forces `Content-Disposition: attachment`.
- `DocumentType` catalog: `review_period_months`, `warning_thresholds_days` (default 90/30/14/7), `requires_acknowledgement`, `safety_domain`, `subject_kind`.
- `SafetyDomain` enum: `occupational, industrial, labour, fire, environmental, road, dangerous_goods`.
- Permissions `compliance_document:*` in `backend/core/domain/value_objects/permission.py`; roles `admin | member | auditor` in `role.py` / `role_permissions.py`; audit family `backend/core/domain/security_events/families/compliance.py` (`compliance.document.*`).
- Latest migration: `0013_compliance_documents`.
- Frontend: Next.js 15 / React 19, TanStack Query, zod, MSW; feature `features/compliance-documents` is the reference slice; navigation in `frontend/src/lib/navigation.ts` (group «Соответствие» → «Документы»); tokens in `frontend/src/theme/tokens/tokens.json` (semantic `light` / `dark`).
- No `compliance_curator` role yet (planned in P11-009). `openpyxl` is not a dependency.

### Defect fixed by this task: «ТрБез» is transport security

«ТрБез» means **транспортная безопасность** (16-ФЗ, ПП РФ № 1640). The P11 plan translated it as "labour safety"; as a result `SafetyDomain.LABOUR` exists, is labelled «Трудовое право» in the UI, and the workbook maps section «10 Транспортная безопасность» to `labour`. No seeded document type uses `labour`. Phase 1 replaces it with `transport_security`.

---

## Decisions (accepted by the product owner)

| # | Topic | Decision |
|---|---|---|
| D1 | Signed scans after approval vs P11-001 D6 | New file role `signed_scan` attachable in `approved`, `active`, `under_review`; all other files stay draft-only. Amend ADR-0006 and record the amendment under P11-001 D6. |
| D2 | Place as an aggregate now or wait for P11-009 | `ShelfSlot` is a new aggregate now; P11-009 links `RegulatoryRequirement` → place (many-to-one). |
| D3 | Source of truth after import | SafetyMAIN. Re-import is an idempotent upsert by code that never overwrites fields edited in SafetyMAIN since the previous import; such rows are reported as conflicts. |
| D4 | Acknowledgement priority | Pull the `acknowledge_document` slice of P11-006 forward: P11-004 (with its worker prerequisite, ADR-0007) → P11-005 (acknowledgement journal only) → P11-006 slice → phase 5 of this task. The slice does not wait for P11-003: the printable acknowledgement sheet (P11-003 template) is not required for electronic acknowledgement and follows later. Recorded on 2026-11-05 in TASK-P11-005 §9 (acknowledgement journal slice, phase 0) and TASK-P11-006 §7 (slice, phase 0); the epic task sequence and critical path are updated. |
| D5 | "Who must be acquainted" | Positions are coded by `Employee.position_code` (P11-004), normalised against the `role` entries of `tag_vocabulary` (P11-002 D14). Recorded as TASK-P11-004 §8 (position codes, unmatched-positions report, minimal catalogue if `tag_vocabulary` is not ready) and TASK-P11-006 §7 (`DocumentApplicability.positions` reference those codes; migration maps existing free text where it matches). Documents whose applicability is still free text show «Область применения не привязана к должностям» instead of coverage. |
| D6 | Places kept on employees / vehicles | Shown on the shelf; aggregate coverage («есть у 18 из 21») arrives with P11-008 §6 (`GET /document-types/{code}/coverage`). Until then their status is the curated one. |
| D7 | Layout | Overview of all sections as strips («Спектр»); a click opens the shelf as a bookcase split into sub-shelves by subsection; a click on a spine opens the place panel (accepted 2026-11-05). |
| D8 | Spine label | Short title on the spine (field `short_title`), full title on hover/focus tooltip and in the panel; code in IBM Plex Mono. |
| D9 | Palette | Graphite = Есть, forest green + bookmark ribbon = В работе, muted ochre = Пересмотр, dotted outline = Уточнить, burgundy dashed outline = Нет; exact tokens in §5.3. |
| D10 | Background | «Тёплая бумага» — flat warm paper on the shelf content area only; shell, navigation, and the place panel keep the global theme. |
| D11 | Excluding places | Curators exclude one or many places with a reason and a mandatory comment; places stay on the shelf as excluded (ghost spines), are restorable, and «Не применимо» from the workbook imports as excluded. |
| D12 | Readiness | `(present + excluded) / total places`, consistent with the workbook formula. |

---

## Scope

The scope is split by implementation phase (§8). Each phase is independently reviewable and mergeable.

### 1. Phase 1 — Transport security domain

1. `SafetyDomain`: remove `LABOUR = "labour"`, add `TRANSPORT_SECURITY = "transport_security"` (`backend/core/domain/value_objects/compliance_enums.py`).
2. Migration `0014_transport_security_domain`: `UPDATE document_types SET safety_domain = 'transport_security' WHERE safety_domain = 'labour'`; drop and recreate `ck_document_types_safety_domain` with the new list. Downgrade reverses both. Any other table that stores `safety_domain` at the time of planning gets the same treatment (planning confirms there is none besides `document_types`).
3. Update every reference: `backend/api/schemas/compliance_documents.py`, `backend/core/infrastructure/persistence/sqlalchemy/models/document_type_model.py`, `frontend/src/features/compliance-documents/types/compliance-documents-dto.ts`, `.../schemas/compliance-documents-response-schemas.ts`, `.../utils/status.ts` (label «Транспортная безопасность»).
4. Fix the wording «ТрБез = labour safety» in `EPIC-P11-compliance-documentation.md` (business goal list) and TASK-P11-001 (§2 domain list), and in the project plan document `SafetyMAIN_Compliance_Documents_Plan.md`. («Minlabour» in P11-003 / P11-009 means Минтруд and stays.)
6. Naming note: Hazard already has `SafetyDirection.TRANSPORT_SAFETY = "transport_safety"` with the same Russian label. The codes differ on purpose: `SafetyDomain.transport_security` is the compliance domain of 16-ФЗ (security against acts of unlawful interference), the hazard direction is about transport safety. Planning may add distinct labels if both appear on one screen.
7. Tests: update `tests/domain/test_document_type.py` (uses `SafetyDomain.LABOUR`); enum values, API schema rejects `labour`, migration up/down on a database containing a `labour` row (`-m db`), frontend label test.

### 2. Phase 2 — Shelf domain, persistence, API

#### 2.1. Domain model

New identities in `safety_ids.py`: `ShelfSectionId`, `ShelfSubsectionId`, `ShelfSlotId`.

**`ShelfSection`** (organisation-owned catalogue entity, like `DocumentType`):

| Field | Type | Rules |
|---|---|---|
| `code` | str | `^[А-ЯЁа-яё]{2,6}$`, unique per organisation, immutable |
| `number` | int | 1–99, unique per organisation, shelf order |
| `title` | str | non-empty |
| `safety_domain` | `SafetyDomain` | used for filtering and reporting |
| `subsections` | ordered tuple of `ShelfSubsection(id, code, title, position)` | `code` = `SECTION.SS`, `SS` two digits, unique within the section |

**`ShelfSlot`** (aggregate root):

| Field | Type | Rules |
|---|---|---|
| `id`, `organization_id` | ids | frozen |
| `code` | `ShelfSlotCode` VO | `^[А-ЯЁа-яё]+\.\d{2}\.\d{2}$`; prefix = section code, `SECTION.SS` = an existing subsection; unique per organisation including excluded places; immutable |
| `section_id`, `subsection_id` | ids | derived from the code at creation |
| `title` | str | 1–500 chars |
| `short_title` | str | 1–40 chars; label on the spine (two vertical lines of about 20 characters) |
| `document_kind` | str | value of the curated vocabulary «Вид» (Политика, Положение, Порядок / процедура, Приказ, Инструкция, Программа, План, Журнал, Перечень, Протокол, Акт, Проект / паспорт, Карта / реестр, Удостоверение / свидетельство, Договор / полис, Отчёт, Разрешение / лицензия); metadata, not an enum, validated against a configurable list |
| `kept_on` | enum `SlotKeptOn` | `organization | facility | event | employee | asset | profession` |
| `obligation_level` | enum | `mandatory | conditional | recommended` |
| `applicability_condition` | str | required when `conditional` |
| `legal_basis` | VO `SlotLegalBasis` | `regulation` (text), `clause`, `quote`, `source_url`, `confidence` (`verified | secondary | unconfirmed | none`) |
| `review_cycle_text` | str | free text («5 лет», «при изменениях») |
| `review_period_months` | int ≥ 1 or null | |
| `curated_status` | enum | `present | present_needs_review | in_progress | missing | to_clarify` |
| `document_type_code` | str or null | must exist in the organisation's `DocumentType` catalog when set |
| `proposed_document_type` | str | workbook values marked «(новый)», kept for curator follow-up |
| `responsible_text`, `legacy_location`, `notes`, `package_code`, `legacy_code` | str | carried from the workbook |
| `exclusion` | VO `SlotExclusion` or null | `reason` (`not_applicable | condition_not_met | duplicate | other`), `comment` (≥ 5 chars after trim, ≤ 1000), `status_before` (`CuratedSlotStatus`), `excluded_by`, `excluded_at` |
| `linked_document_ids` | ordered set of `ComplianceDocumentId` | current and previous editions |
| `import_fingerprint`, `last_imported_at` | str, datetime | see §4.4 |
| `created_*`, `updated_*`, `version` | | optimistic concurrency like `ComplianceDocument` |

Domain methods (each raises a domain exception on an invalid transition):

- `create(...)` — validates code against section/subsection.
- `update_details(...)` — curated fields; not `code`, not `exclusion`.
- `exclude(reason, comment, actor, at)` — only when not excluded; stores `status_before`.
- `restore(actor, at)` — only when excluded; `curated_status = status_before`; places imported as «Не применимо» have `status_before = to_clarify`.
- `confirm_applicable(actor, at)` — only from `to_clarify` and not excluded → `missing`.
- `link_document(document)` — same organisation; document `subject_kind = organization` (employee/asset documents are P11-008); idempotent.
- `unlink_document(document_id)`.

Domain events: `ShelfSlotCreated`, `ShelfSlotUpdated`, `ShelfSlotExcluded`, `ShelfSlotRestored`, `ShelfSlotApplicabilityConfirmed`, `ShelfSlotDocumentLinked`, `ShelfSlotDocumentUnlinked`.

#### 2.2. Effective status (application service, backend-authoritative)

`ShelfStatusEvaluator.evaluate(slot, linked_documents, document_type, today) -> ShelfEffectiveStatus`; `ClockContract` only provides `now()`, so `today` = the UTC date of `now()`, as in P11-001 D11. First matching rule wins:

1. `excluded` — the place is excluded.
2. A linked document is `active` or `under_review` (the current edition = the most recent `effective_from` among them):
   - `under_review` if the document is `under_review`;
   - `overdue_review` if review date < today, where review date = `next_review_at`, else `effective_from + review_period_months` (document type, else slot);
   - `review_due` if review date − today ≤ the largest value of the type's `warning_thresholds_days` (default 90);
   - otherwise `present`.
3. A linked document is `draft` or `approved` only → `in_progress`.
4. Otherwise from `curated_status`: `present` → `present_unverified` (curated, no document in SafetyMAIN); `present_needs_review` → `review_due`; `in_progress` → `in_progress`; `missing` → `missing`; `to_clarify` → `to_clarify`.

Known divergence to document in `DocumentShelf.md`: P11-001 D11 treats a document as review-due only when its type has `review_period_months`; the shelf additionally falls back to the place's `review_period_months`, so the shelf can show «Пересмотр» while the document page does not. Planning may instead align both by reading the same rule from one service.

Presentation groups used by UI and counts: «Есть» = `present`, `present_unverified`; «Пересмотр» = `review_due`, `overdue_review`, `under_review`; «В работе» = `in_progress`; «Нет» = `missing`; «Уточнить» = `to_clarify`; «Исключено» = `excluded`. Readiness per D12 counts «Есть» + «Исключено».

`available_actions` (computed by the backend for the current user, drives buttons; the frontend never infers them):

| Effective status | Primary action | Other actions (curator) |
|---|---|---|
| `missing` | `develop_document` | `link_document`, `exclude` |
| `to_clarify` | `confirm_applicable` | `exclude` (default reason `condition_not_met`) |
| `in_progress` | `open_project` | `link_document`, `exclude` |
| `present_unverified` | `upload_scan` (creates the document, §4.5) | `link_document`, `exclude` |
| `present` | `send_for_acknowledgement` (phase 5; before that `open_document`) | `exclude` |
| `review_due`, `overdue_review` | `start_review` | `exclude` |
| `under_review` | `open_document` | `exclude` |
| `excluded` | `restore` | — |

Users without `shelf:curate` get only `open_document` / `open_project` where applicable.

#### 2.3. Persistence — migration `0015_document_shelf`

- `shelf_sections`: `id` PK, `organization_id` FK NOT NULL, `code`, `number`, `title`, `safety_domain` (CHECK as in `document_types`), timestamps, `version`. Unique `(organization_id, code)`, `(organization_id, number)`.
- `shelf_subsections`: `id` PK, `organization_id`, `section_id` FK ON DELETE RESTRICT, `code`, `title`, `position`. Unique `(organization_id, code)`.
- `shelf_slots`: all fields of §2.1; enums as text + CHECK; `legal_basis` columns flattened (`basis_regulation`, `basis_clause`, `basis_quote`, `basis_source_url`, `basis_confidence`); exclusion columns nullable with a CHECK that all exclusion columns are either all null or all set; `comment` length CHECK. Unique `(organization_id, code)`. Indexes: `(organization_id, section_id)`, `(organization_id, subsection_id)`.
- `shelf_slot_documents`: `organization_id`, `slot_id` FK CASCADE, `document_id` FK RESTRICT, `linked_at`, `linked_by`; PK `(slot_id, document_id)`; index `(organization_id, document_id)`.
- SQLAlchemy models, mappers, repositories (`ShelfSectionRepository`, `ShelfSlotRepository` with `list_by_section`, `search(q)`, `get_by_code`), wired into the unit of work; in-memory repositories for non-DB tests; alembic head test updated.
- No physical DELETE anywhere; sections and subsections are only created or renamed.

#### 2.4. Authorization and audit

- `SystemPermission.SHELF_READ = "shelf:read"` → `admin`, `member`, `auditor`.
- `SystemPermission.SHELF_CURATE = "shelf:curate"` → `admin` now; P11-009 maps it to `compliance_curator`.
- Permissions are role-based: linking a document additionally requires the role to hold `compliance_document:read`, and the document must belong to the same organisation (else 404).
- Cross-organisation access to any shelf resource → 404.
- Audit events in the `compliance` family. Identifiers must match `^[a-z]+\.[a-z]+\.[a-z]+$` (`backend/core/domain/security_events/naming.py`), so the subject is the single word `place` / `section` / `shelf`: `compliance.place.created | updated | excluded | restored | confirmed | linked | unlinked`, `compliance.section.created | updated`, `compliance.shelf.imported` (one per non-dry-run import, payload = counts and source file SHA-256). `excluded` carries reason and comment; `confirmed` = applicability confirmed. No new legacy identifiers.
- Registry changes this requires: `_compliance_descriptor` in `families/compliance.py` currently hardcodes `SecurityEventSubjectDomain.COMPLIANCE_DOCUMENT` — add a `subject_domain` parameter; new `SecurityEventSubjectDomain.SHELF` (or `SHELF_PLACE`), new `AuditResourceType` values for places and sections (`audit_resource_type.py`), new `AuditAction` values for exclude / restore / confirm / link / unlink / import (`audit_action.py`). Exact names fixed in planning against `docs/architecture/AuditTaxonomy.md`.

#### 2.5. REST API (`backend/api/routers/shelf.py`, prefix `/shelf`)

```text
GET   /api/v1/shelf                                   overview: sections with counts
GET   /api/v1/shelf/sections/{section_code}/slots     slots of one shelf
GET   /api/v1/shelf/slots?q=&limit=50                 search across all shelves (code or title)
GET   /api/v1/shelf/slots/{slot_id}                   place detail
POST  /api/v1/shelf/slots                             create (curate)
PATCH /api/v1/shelf/slots/{slot_id}                   edit curated fields (curate)
POST  /api/v1/shelf/slots/{slot_id}/exclude           (curate)
POST  /api/v1/shelf/slots/{slot_id}/restore           (curate)
POST  /api/v1/shelf/slots/bulk-exclude                (curate)
POST  /api/v1/shelf/slots/{slot_id}/confirm-applicable (curate)
POST  /api/v1/shelf/slots/{slot_id}/documents         link {document_id, version} (curate)
POST  /api/v1/shelf/slots/{slot_id}/documents/{document_id}/unlink  {version} (curate)
POST  /api/v1/shelf/slots/{slot_id}/develop          create a draft ComplianceDocument from the place and link it atomically (curate + compliance_document:create)
```

DTOs (fields in snake_case; exact shapes fixed during planning):

- `ShelfOverviewDto`: `sections[]`, `totals {places, excluded, by_group{present, review, in_progress, missing, to_clarify, excluded}, readiness_percent}`, `evaluated_at`.
- `ShelfSectionSummaryDto`: `code, number, title, safety_domain, total, mandatory_total, by_group{…}, readiness_percent, strip[]` where `strip` = `{code, group}` per place in code order (drives the overview strip without a second request; ~416 items in total).
- `ShelfSlotSummaryDto`: `id, code, subsection_code, short_title, title, document_kind, kept_on, obligation_level, effective_status, group, has_acknowledgement_gap` (always `false` before phase 5).
- `ShelfSectionSlotsDto`: `section {code, number, title}`, `subsections[] {code, title, slots[]}`.
- `ShelfSlotDetailDto`: summary fields + `legal_basis{…}`, `applicability_condition`, `review_cycle_text`, `review_period_months`, `review_date`, `curated_status`, `exclusion{reason, comment, excluded_by_name, excluded_at}|null`, `current_document{id, code, title, status, effective_from, next_review_at, approved_by_order{code,title}|null, signed_scan{file_id, content_type, size_bytes, uploaded_at}|null, working_file{…}|null}|null`, `editions[]{id, code, status, effective_from}`, `available_actions[]`, `primary_action`, `acknowledgement` (phase 5, else `null`), `version`.
- `ExcludeSlotRequest {reason, comment, version}`; `BulkExcludeRequest {items[{slot_id, version}], reason, comment}` — all-or-nothing in one unit of work, ≤ 200 items; one audit event per place; response lists updated summaries.
- `DevelopSlotRequest {document_type_code?, version}` → creates a `draft` ComplianceDocument with `code` = place code, `title` = place title, type = request value or the place's `document_type_code`, source `manual`; links it in the same unit of work; returns `{document_id, slot}`. Without any type → 422 `document_type_required` (the panel then asks for the type).
- No DELETE endpoints (epic convention); unlinking is a POST command and keeps an audit trail.
- Errors: 403 without permission, 404 unknown or foreign, 409 version conflict (bulk: reports the conflicting slot ids), 422 validation (`comment_too_short`, `already_excluded`, `not_excluded`, `not_to_clarify`, `document_subject_not_supported`, `document_type_required`, `already_linked_active_document`).
- Docs: `docs/api/ShelfAPI.md`.

### 3. Phase 3 — Workbook import

#### 3.1. Command

```bash
python scripts/import_shelf_workbook.py --organization-id <uuid> --file <path.xlsx> --actor-email <curator> [--dry-run] [--report <path.json>]
```

- Runs through application handlers (same audit as the API, actor = the given curator). `openpyxl` is added to a new optional extra `import` and to `dev`.
- Reads sheet «Полка», locates the header row by header names (not by index), maps by names; a missing required header aborts with a clear message.
- `--dry-run` writes nothing and prints the same report.

#### 3.2. Column mapping

| Workbook header | Field | Notes |
|---|---|---|
| Код | `code` | required |
| Раздел | section `number` + `title` | «05 Взрывчатые материалы и БВР» → 5, «Взрывчатые материалы и БВР» |
| Подраздел | subsection `title` | code = first two parts of `code` |
| Документ (место на полке) | `title`; `short_title` generated (§3.3) | required |
| Вид | `document_kind` | vocabulary from sheet «Справочники» |
| Ведётся на | `kept_on` | Организация → organization; ОПО / объект → facility; Событие → event; Работник → employee; ТС / техника → asset; Профессия / вид работ → profession |
| Обязательность | `obligation_level` | Обязателен / Обязательна → mandatory; При условии → conditional; Рекомендуется → recommended |
| Условие применимости | `applicability_condition` | required for conditional |
| Основание (НПА), Пункт / статья, Выдержка из НПА, Ссылка на текст, Достоверность основания | `legal_basis.*` | confidence: «сверено по тексту…» → verified; «вторичный источник» → secondary; «не подтверждено» → unconfirmed; «—»/empty → none; other free text → verified when it starts with «сверено» or «проверка отдельным агентом», else secondary, original text appended to `notes` |
| Цикл / периодичность, Период, мес | `review_cycle_text`, `review_period_months` | |
| Статус | `curated_status` / exclusion | Есть → present; Есть — нужен пересмотр → present_needs_review; В работе (проект) → in_progress; Нет → missing; Уточнить → to_clarify; Не применимо → excluded with reason `not_applicable`, comment «Статус «Не применимо» из реестра-полки», `status_before = to_clarify` |
| Тип в SafetyMAIN | `document_type_code` or `proposed_document_type` | existing code → link; «(новый)», «журнал (P11-005)» etc. → proposed text |
| Домен SafetyMAIN | section `safety_domain` | `labour` → `transport_security`; all rows of a section must agree, else error |
| Где лежит сейчас, Ответственный, Примечание, Код в версии 1, Пакет / категория | `legacy_location`, `responsible_text`, `notes`, `legacy_code`, `package_code` | |
| Дата утверждения / выдачи, Следующий пересмотр, Дней до пересмотра | ignored | dates belong to documents, not places |

Unknown vocabulary values are rejected with row number and value — never guessed.

#### 3.3. Short title generation

Deterministic, ≤ 40 characters: strip parenthesised fragments; apply the abbreviation list (охрана/охраны/охране труда → ОТ, инструкция по охране труда → ИОТ, промышленной безопасности → ПБ, пожарной безопасности → ПожБ, транспортной безопасности → ТрБ, безопасности дорожного движения → БДД, транспортных средств → ТС, взрывчатых материалов → ВМ, «Приказ о назначении» → «Назначение», «Журнал регистрации» → «Журнал», «ответственного» → «отв.»); cut at a word boundary with «…». The curator can edit it; an edit counts as a SafetyMAIN edit for D3. The prototype showed that automatic shortening is often poor («Приказ о назначении…»), so the curator guide recommends reviewing short titles per section.

#### 3.4. Idempotency and conflicts (D3)

- `import_fingerprint` = SHA-256 of the normalised mapped values of the row.
- Row new → create. Fingerprint unchanged → unchanged. Fingerprint changed and the slot was not modified since `last_imported_at` (no `updated_at` later than it by a non-import actor) → update. Changed and modified in SafetyMAIN → **conflict**, not applied, listed with field-level differences.
- Places present in SafetyMAIN but absent from the workbook are reported, never excluded automatically.
- Report: created / updated / unchanged / conflicts / rejected rows / missing-in-workbook, human-readable and optional JSON.

#### 3.5. Tests

A synthetic workbook generated in the test (never the real file): header detection, every vocabulary mapping, the «Обязательна» spelling variant, labour → transport_security, conditional without condition → rejected, re-run idempotency, conflict detection, dry-run writes nothing, audit event emitted once per real run.

### 4. Phase 4 — Frontend «Полка», signed scans, optional scan attachment

#### 4.1. Signed scan (D1)

- `DocumentFile.role`: `working | signed_scan` (default `working`); migration `0016_document_file_role` adds the column with default and CHECK.
- `POST /compliance-documents/{id}/signed-scan/upload-url` and `/signed-scan/confirm` — allowed in `approved`, `active`, `under_review`; same SHA-256 / size / MIME rules as P11-001 D3 / D20; PDF, JPEG, PNG only; permission `compliance_document:update`; audit `compliance.document.signed_scan_attached`. A new signed scan supersedes the previous one as the current signed scan; history is kept and visible in versions.
- `ComplianceDocument.current_file` (today `files[-1]`) is redefined as **the last `working` file**; add `current_signed_scan` = the last `signed_scan`. `approve` / `activate` preconditions and `files/current/download-url` keep using the working file; new `files/signed-scan/current/download-url` mirrors it for scans. `files/versions` returns both roles with `role`. Domain and API tests cover that a signed scan never changes the working-file preconditions.
- `GET /compliance-documents/{id}/files/{file_id}/view-url` — presigned GET with `Content-Disposition: inline` for in-browser rendering (the existing download URL stays `attachment`).
- Object storage CORS already admits `GET` from the application origin (`ApplicationServerDeployment.md` CORS rule; `MINIO_API_CORS_ALLOW_ORIGIN` in `docker-compose.yml`). Phase 4 verifies inline rendering with pdf.js on MinIO and Yandex Object Storage and, if range requests are used, adds `range` to `AllowedHeaders` and `Content-Range`, `Accept-Ranges`, `Content-Length` to `ExposeHeaders` (or configures pdf.js with `disableRange`). The runbook is updated accordingly.
- ADR-0006 amendment section and a note under P11-001 D6.

#### 4.2. Route, navigation, structure

- Route `frontend/src/app/shelf/page.tsx`; URL state `?section=ТрБ&slot=ТрБ.02.02&filter=problems&excluded=hidden` (shareable, restored on load, back/forward works).
- Navigation: child «Полка» under «Соответствие» after «Документы», `requiredPermission: "shelf:read"`.
- Feature `frontend/src/features/document-shelf/` with `api/` (shelf-api, queries, mutations, query keys), `types/` (DTOs), `schemas/` (zod response schemas), `hooks/` (`use-shelf-permissions`, `use-shelf-url-state`), `components/`, `pages/shelf-page.tsx`, `index.ts`. Respects dependency-cruiser rules: no imports of other features' internals; the scan viewer obtains URLs through this feature's API module calling the documented compliance endpoints.
- Shared, domain-agnostic: `components/document-viewer/PdfViewer` (pdf.js via `pdfjs-dist`, pinned; worker loaded lazily; page thumbnails; zoom; keyboard paging; images rendered as `<img>`; fallback «Скачать» for other types).

#### 4.3. Screen composition (prototype = reference)

Content area background `shelf-page-bg`; shell, top bar, and the place panel keep global tokens.

1. **Header**: «Полка документов», subline «N мест в 13 разделах · исключено M · реестр сверен с НПА [дата импорта]»; filter chips «Все места / Проблемные / Обязательные» (`aria-pressed`); toggle «Исключённые видны / скрыты».
   - «Проблемные» = groups «Нет», «Пересмотр», plus `has_acknowledgement_gap`. «Обязательные» = `mandatory`, not excluded. Non-matching places are dimmed (opacity 0.22), not removed, so the shelf keeps its shape.
2. **Summary**: «Готовность» (percent + bar) and counts «Есть», «В работе», «Пересмотр», «Нет», «Уточнить», each with its spine swatch.
3. **Overview «Все разделы»**: one row per section (button, `aria-expanded`): number, title, strip of thin bars (one per place, code order, colour by group, excluded hidden when toggled off), «N из M», percent. Clicking opens the shelf below and selects its first place.
4. **Opened shelf**: section number (mono, muted), title, «N из M в порядке · K обязательных · исключено X»; legend; button «Выбрать несколько»; sub-shelves by subsection in a wrapping grid, each with `SS` code + subsection title, spines, and a plank.
5. **Spine** (`<button>`):
   - width by `document_kind` (Журнал 30, Проект / паспорт 32, План 30, Карта / реестр 28, Перечень 28, Положение 28, Порядок / процедура 26, Инструкция 26, Программа 26, Политика 26, Отчёт 24, Акт 24, Протокол 24, Договор / полис 24, Приказ 22, Удостоверение / свидетельство 22, Разрешение / лицензия 22; default 24 px);
   - height by `obligation_level` (mandatory 136, conditional 114, recommended 98 px); excluded: 12 × 70 px dashed ghost, no label;
   - vertical label `short_title`, 10/11 px, bottom-to-top;
   - bookmark ribbon above «В работе»; a 7 px dot above when `has_acknowledgement_gap`; a caret below the selected spine; selection checkbox overlay in selection mode;
   - hover/focus lifts by 6 px in 150 ms (none with `prefers-reduced-motion`); tooltip on hover and keyboard focus: code (mono), full title, subsection · kind · obligation, status, acknowledgement summary.
6. **Place panel** (right column ≥ 1200 px, below the shelf on narrower screens, full-screen sheet on phones):
   - header: code, status badge (same shape language as spines), title, «подраздел · вид · обязательность»;
   - scan block when a file exists: thumbnails + first page via `PdfViewer`, buttons «Открыть на весь экран», «Скачать»; label «Скан подписанной редакции» or «Рабочий файл (без подписи)»;
   - empty states: «Место есть, документа нет» (missing), «Нужно уточнить применимость» (to_clarify), «Проект в работе» (in_progress), «Исключено с полки» with reason, comment, who and when;
   - details: Основание, Пункт, Пересмотр, Редакция, Приказ об утверждении, Редакции (archive);
   - acknowledgement block (phase 5, §5);
   - actions from `primary_action` / `available_actions`; destructive-looking «Исключить с полки» as a text button in the danger colour.
7. **Excluding** (curators): in-panel form (no modal): codes, title «Исключить место с полки» / «Исключить N мест с полки», explanation, warning when documents are linked («Документ останется в разделе «Документы», ознакомление по нему продолжится»), radio group of reasons, comment (`<textarea>`, required, inline error «Напишите, почему место не нужно: это увидят при проверке.»), buttons «Исключить» / «Отмена». Bulk: «Выбрать несколько» → selection mode → bar «Выбрано N мест · Исключить выбранные · Снять выбор». After success: inline `role="status"` line «Исключено N мест: codes» with «Отменить» (calls restore with the returned versions). For «Уточнить»: «Применимо — нужен документ» / «Не применимо».
8. **«Разработать»** calls `POST /shelf/slots/{id}/develop` (asking for the document type in the panel when the place has none) and navigates to the new draft's edit page `/compliance-documents/{id}/edit`; the existing create page is not changed. **«Загрузить скан»** for `present_unverified` calls the same endpoint, then opens the upload dialog in the panel; approve / activate follow the existing lifecycle actions on the document page. The upload dialog is reused by exporting `ComplianceDocumentUploadDialog` from `features/compliance-documents/index.ts` (public API, allowed by `.dependency-cruiser.cjs`); the shelf feature calls compliance endpoints only through its own `api/` module.
9. **Search** in the top bar: `GET /shelf/slots?q=` results dropdown; choosing a result opens its section and place.
10. Loading: skeleton strips and spines; errors via the existing `Alert` + retry; empty organisation (no import yet): invitation «Загрузите реестр-полку» with a link to the curator guide.

#### 4.4. Responsive and accessibility

- ≥ 1200 px: shelf and panel side by side; 768–1199 px: panel below the shelf; < 768 px: overview strips hide the counts column, sub-shelves scroll horizontally inside their own box, the panel is a full-screen sheet with a close button.
- WCAG 2.2 AA per `docs/design/Accessibility.md`: all spines and rows are real buttons; tooltips also on focus; status never colour-only (fill pattern + text in tooltip/badge + ribbon); keyboard: Tab through spines, Enter opens, Escape closes the sheet/form; focus returns to the spine after closing.

#### 4.5. Optional scan attachment script

`scripts/attach_shelf_scans.py --organization-id --root <dir> --actor-email [--dry-run]` (dry-run by default): for places with `curated_status = present`, no linked document, a `document_type_code`, and a PDF at `legacy_location` under `--root` — create a draft `ComplianceDocument` (code = place code, title = place title), upload the PDF as the working file, approve and activate through the existing handlers, link to the place. Never moves, renames, or deletes source files. Report: attached / skipped with reason.

### 5. Phase 5 — Acknowledgement coverage

- `ShelfSlotDetailDto.acknowledgement` for the current document when its type `requires_acknowledgement`: `{document_id, edition_effective_from, required_total, acknowledged_total, overdue_total, pending[{employee_id, full_name, position_title, manager_full_name, due_date, overdue}], applicability_resolved}` — taken as is from `GET /compliance-documents/{id}/acknowledgement-coverage` (TASK-P11-006 §7); the acknowledged list (date, edition) comes from `GET /compliance-documents/{id}/acknowledgements` (TASK-P11-005 §9). The shelf adds no calculation.
- `has_acknowledgement_gap` on summaries; section summaries gain `not_acknowledged_documents`.
- Panel: «Ознакомление N из M», progress bar, «Не ознакомлены — должны по роду деятельности» list (overdue first, with line manager), «Ознакомлены» expandable list with date and edition, `applicability_resolved = false` → «Область применения не привязана к должностям». «Напомнить» calls the P11-007 endpoint when it exists, otherwise hidden. A new edition resets coverage to that edition (obligation semantics of P11-006).
- Personal data shown: full name, position, manager — within the epic's allowed set.

### 6. Design tokens (§D9, D10)

Semantic colours in `tokens.json` reference primitives (`{palette.*}`); the shelf follows that rule. New primitive families in `primitive.palette`: `paper` (`#F7F4EE`, `#FFFDF9`, `#E4DED2`, `#CFC8BA`, `#6B665C`, `#B4B0A6`, `#4A4740`, `#3A3D38`, `#262925`, `#1F2220`), `graphite` (`#3B3B3B`, `#6E6E6E`), `forest` (`#213C30`, `#437B62`), `ochre` (`#E9D6A8`, `#C9A45E`, `#A47A2C`, `#5A4316`, `#5A3F0E`, `#E0C27E`, `#F3E3C3`), `brick` (`#87251E`, `#CA372D`, `#EADBD5`, `#342522`) — stop names fixed in planning. The semantic tokens below (`semantic.light.color` / `semantic.dark.color`) reference them and are consumed via CSS variables only. Values: Dark values reach ≥ 3:1 against `shelf-page-bg` for non-text graphics; spine text keeps ≥ 4.5:1.

| Token | Light | Dark | Meaning |
|---|---|---|---|
| `shelf-page-bg` | `#F7F4EE` | `#1F2220` | Shelf content background («Тёплая бумага») |
| `shelf-ink` | `#6B665C` | `#B4B0A6` | Secondary text on the shelf background |
| `shelf-card-bg` / `shelf-card-border` | `#FFFDF9` / `#E4DED2` | `#262925` / `#3A3D38` | Summary and overview cards |
| `shelf-plank` | `#CFC8BA` | `#4A4740` | Shelf board |
| `shelf-present-bg` (= border) | `#3B3B3B` | `#6E6E6E` | Есть |
| `shelf-progress-bg` (= border) | `#213C30` | `#437B62` | В работе |
| `shelf-spine-fg` | `#F5F3EC` | `#F5F3EC` | Text on present / progress spines |
| `shelf-progress-ribbon` | `#C9A45E` | `#E0C27E` | Bookmark ribbon |
| `shelf-review-bg` / `-border` / `-fg` | `#E9D6A8` / `#C9A45E` / `#5A3F0E` | `#5A4316` / `#A47A2C` / `#F3E3C3` | Пересмотр |
| `shelf-missing-border` (= fg) | `#87251E` | `#CA372D` | Нет, dashed 1.5 px |
| `shelf-missing-bg` | `#EADBD5` | `#342522` | Tint of an empty place |
| `shelf-clarify-border` | `{palette.slate.400}` | `{palette.slate.400}` | Уточнить, dotted 1.5 px |
| `shelf-excluded-border` | `#CFC8BA` | `#4A4740` | Исключено, dashed 1 px |
| `shelf-ack-dot` | `#87251E` | `#CA372D` | Not everyone acquainted |

Typography: IBM Plex Sans (UI), IBM Plex Mono (codes, numbers). Primary actions keep the global interactive tokens (teal).

### 7. Documentation

- `docs/architecture/DocumentShelf.md` — place vs document vs requirement, effective status rules, readiness, exclusion semantics, import contract.
- `docs/domain/ShelfSlot.md` (or a section in `ComplianceDocuments.md`) and `UbiquitousLanguage.md`: «полка», «место на полке», «исключённое место».
- `docs/api/ShelfAPI.md`; `ComplianceDocumentsAPI.md` updated for signed scans and view URL.
- `docs/guides/ShelfImport.md` (new `docs/guides/` folder; curator guide: preparing the workbook, dry-run, reading the report, resolving conflicts, reviewing short titles).
- `docs/architecture/AuditTaxonomy.md` (new subject domain, resource types, actions, `compliance.place.*` / `compliance.section.*` / `compliance.shelf.imported`).
- ADR-0006 amendment (signed scans, working vs signed-scan current file, inline view URL, range/CORS check); `docs/infrastructure/ApplicationServerDeployment.md` (CORS).
- `CLAUDE.md` / `AI_CONTEXT.md`: new aggregate, router, scripts, `openpyxl` extra, `pdfjs-dist`.

---

## Acceptance Criteria

Phase 1
1. `labour` does not exist in backend, database (after migration), API schemas, or frontend; `transport_security` is accepted everywhere with the label «Транспортная безопасность»; migration up/down passes on a database containing a `labour` row.

Phase 2
2. A slot cannot be created with a code that does not match its section/subsection or duplicates any existing code (including excluded places).
3. Every rule of §2.2 is covered by unit tests with a fixed clock; the frontend contains no status, readiness, or available-action calculation.
4. `GET /shelf` returns 13 sections with counts and readiness matching the evaluator; `GET /shelf/sections/ТрБ/slots` returns 14 places grouped by 6 subsections (after the real import).
5. Exclude, restore, bulk-exclude, confirm-applicable, link, unlink, and develop enforce their preconditions (422 codes of §2.5), optimistic concurrency (409), `shelf:curate` (403), and tenant isolation (404); each emits its audit event; bulk-exclude is all-or-nothing.

Phase 3
6. Dry-run of the current workbook reports 416 places in 13 sections, 92 subsections, 3 excluded, zero rejected rows; a real run creates them and emits one `compliance.shelf.imported`; an immediate second run reports 416 unchanged.
7. A place edited in SafetyMAIN and changed in the workbook is reported as a conflict and not overwritten.

Phase 4
8. `/shelf` renders the overview, opened shelf, and place panel per §4.3 with the tokens of §6 in light and dark themes; URL state round-trips.
9. A place with an active document and a signed scan shows the scan inline (pdf.js, thumbnails) via an inline presigned URL; no file bytes pass through the API; a document without a signed scan shows its working file labelled «Рабочий файл (без подписи)».
10. A signed scan can be attached to an `active` document; attaching any other file to a non-draft document is still rejected.
11. A curator excludes one place and several places with a reason and a comment, sees them as ghost spines, hides/shows them, undoes the action, and restores a place from its panel; a comment shorter than 5 characters shows the inline error and is also rejected by the backend; a viewer without `shelf:curate` sees exclusion details but no actions.
12. Keyboard-only and screen-reader walkthrough of overview → shelf → spine → panel → exclude form passes; statuses are distinguishable in greyscale.
13. `npm run verify` passes; backend suite passes including `-m db`.

Phase 5
14. For a document requiring acknowledgement, the panel lists exactly the employees with open `acknowledge_document` obligations for the current edition, split into overdue / pending / acknowledged, matching P11-006 data; a new edition resets coverage; spines show the gap dot.

---

## Non-Goals

- Sheets «План разработки», «Оформить и проверить», «Изменения НПА», «Сводка» (P11-009 / P11-010 or later).
- Legal gap analysis, regulation registry, monitoring (P11-009 / P11-010).
- Generating documents from knowledge blocks (P11-003).
- Employee/asset documents coverage on places (P11-008), notifications (P11-007).
- Editing or annotating scans; OCR of scans.
- A `compliance_curator` role (P11-009); until then curation is admin-only.
- Physical deletion of places, sections, or links' target documents.

---

## Verification

- Backend: domain tests (code VO, lifecycle methods, exclusion invariants, working vs signed-scan current file), evaluator tests with a fixed `ClockContract`, application handler tests (in-memory UoW), API tests (RBAC, 404 cross-tenant, 409, 422 codes, bulk atomicity), audit tests, `pytest -m db` with migrations `0014`–`0016` up/down, alembic head test, architecture tests unchanged.
- Import: synthetic workbook tests (§3.5); a manual dry-run against a copy of the real workbook attached to the review (not committed).
- Frontend: Vitest + MSW for overview, shelf, spine states, panel branches, exclude form validation, bulk selection, undo, URL state; zod schema tests; Playwright: open section → spine → scan visible → exclude with comment → undo → reload keeps state.
- Accessibility: axe checks in Playwright; manual keyboard pass; greyscale screenshot review.
- Visual: compare with the prototype canvas in light and dark.

---

## Suggested implementation phases

| Phase | Content | Depends on | Indicative size |
|---|---|---|---|
| 1 | Transport security domain (§1) | P11-001 | 0.5–1 day |
| 2 | Domain, evaluator, persistence `0015`, permissions, audit, API (§2) | 1 | 4–5 days |
| 3 | Workbook import + curator guide (§3) | 2 | 2 days |
| 4 | Signed scans `0016`, inline view URL, CORS; frontend «Полка» (§4, §6); optional scan attachment script | 2, 3 | 6–8 days |
| 5 | Acknowledgement coverage (§5) | P11-004, P11-005 (acknowledgement journal), P11-006 slice | 2–3 days |

Each phase: plan → implementation → review per `docs/ai/DevelopmentWorkflow.md`; phases 1–4 can ship before P11-004.

---

## Risks and known limitations

| Risk | Mitigation |
|---|---|
| Inline disposition / range requests behave differently on MinIO and Yandex Object Storage | Verify in phase 4 against both; fallback: fetch the inline URL as a blob with `disableRange` |
| `pdfjs-dist` bundle size | Lazy-load the viewer and worker only when the panel shows a PDF |
| Workbook drift (structure or vocabularies change) | Header-name mapping, strict vocabulary validation, dry-run first |
| Poor automatic short titles | Curator review per section (guide), editable field |
| Only admins can curate until `compliance_curator` exists | Accepted limitation; the occupational-safety specialist needs the admin role or waits for P11-009 |
| Acknowledgement depends on three unfinished tasks | Phase 5 isolated; panel shows no acknowledgement block until it ships |
| Curated «Есть» without a document in SafetyMAIN looks complete | Separate `present_unverified` status and the «Загрузить скан» action; the scan attachment script closes the gap in bulk |
