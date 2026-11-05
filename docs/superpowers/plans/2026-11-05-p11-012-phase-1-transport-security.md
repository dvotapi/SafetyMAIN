# TASK-P11-012 Phase 1 (Transport security domain) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the mistranslated compliance safety domain `labour` with `transport_security` («Транспортная безопасность») in the domain enum, database (migration `0014_transport_security_domain`), API schemas, and frontend, so that acceptance criterion 1 of TASK-P11-012 holds.

**Architecture:** A pure rename of one enum value across the existing `DocumentType` vertical slice (P11-001). One data + constraint migration on `document_types`; no new aggregates, endpoints, permissions, or audit events. Query-parameter validation already goes through `SafetyDomain`, so the API rejects `labour` once the enum changes.

**Tech Stack:** Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL 17, pytest (`-m db`); Next.js 15, zod, Vitest.

**Spec:** `docs/tasks/TASK-P11-012-document-shelf.md` §1 (Phase 1) and acceptance criterion 1; TASK-P11-001 «Amendments after completion» A1. Where they differ from this plan, the TASK wins.

## Global Constraints

- Migration: `revision = "0014_transport_security_domain"`, `down_revision = "0013_compliance_documents"`; both `upgrade` and `downgrade`.
- `0013_compliance_documents.py` is history and is not edited (it keeps `labour`).
- Only `document_types.safety_domain` stores the value. Verified during planning: no other table, JSONB payload, seed entry (`scripts/seed_document_types.py`), audit payload, MSW fixture, or test fixture uses `labour`.
- `SafetyDirection.TRANSPORT_SAFETY = "transport_safety"` (Hazard) is not touched (TASK §1.6).
- Out of scope: shelf aggregates, any other enum, hazard labels, refactors of compliance-document code.
- All DB tests carry `@pytest.mark.db`. Code, comments, commit messages in English. Branch `claude/p11-012-phase-1-transport-security` from fresh `main`; commit with explicit pathspecs; never stage `.claude/`.

## Decisions taken in this plan (review these)

| # | Decision | Why |
|---|---|---|
| P1 | `TRANSPORT_SECURITY` takes the position of `LABOUR` in every ordered list (enum, Literal, tuples, `SAFETY_DOMAINS`): `occupational, industrial, transport_security, fire, environmental, road, dangerous_goods`. | Keeps the filter dropdown order stable and the diff minimal. |
| P2 | Upgrade order: drop `ck_document_types_safety_domain` → `UPDATE ... 'labour' → 'transport_security'` → create the constraint with the new list. Downgrade: drop → `UPDATE ... 'transport_security' → 'labour'` → create the constraint with the 0013 list. Value lists are literal tuples inside the migration (not imported from the model). | The old constraint rejects the new value, so the update must run between drop and create; migrations must not depend on application code that changes later. |
| P3 | `updated_at` of migrated rows is not changed. | Data correction of a mistranslated code, not a user edit; no audit event either (same as other data migrations). |
| P4 | «`labour` does not exist in the backend» (criterion 1) is read as: not in runtime code, schemas, model, or live database. The string remains only in migrations `0013` (history) and `0014` (downgrade). | Rewriting an applied migration is unsafe; the downgrade needs the old value. |
| P5 | Frontend label is «Транспортная безопасность» only. No disambiguating label for the hazard `transport_safety` — the two never appear on one screen today (TASK §1.6 allows adding it later). | Smallest correct change. |
| P6 | `docs/architecture/ComplianceDocumentPersistence.md` gets one line noting that `0014_transport_security_domain` replaced `labour`; no other architecture doc lists the values. | Keeps the persistence doc accurate. API docs show no enum list, nothing to change there. |
| P7 | TASK §1.4 wording fixes in `EPIC-P11`, `TASK-P11-001`, `TASK-P11-009` are already done in the docs PR (#7). `SafetyMAIN_Compliance_Documents_Plan.md` is not in the repository — see Q1. | Avoid duplicate edits. |

## Affected files

Backend
- Modify: `backend/core/domain/value_objects/compliance_enums.py`
- Modify: `backend/api/schemas/compliance_documents.py` (`SafetyDomainValue`)
- Modify: `backend/core/infrastructure/persistence/sqlalchemy/models/document_type_model.py` (`_SAFETY_DOMAINS`)
- Create: `alembic/versions/0014_transport_security_domain.py`

Tests
- Modify: `tests/domain/test_document_type.py` (`SafetyDomain.LABOUR` → `TRANSPORT_SECURITY`)
- Create: `tests/domain/test_compliance_enums.py` (enum values; `labour` absent; `SafetyDomain("labour")` raises)
- Modify: `tests/api/test_compliance_documents_api.py` (list filter `safety_domain=labour` → 422; `transport_security` accepted)
- Modify: `tests/api/test_document_types_api.py` (response serializes `transport_security`)
- Create: `tests/infrastructure/test_transport_security_domain_migration.py` (module test; `-m db` up/down with a `labour` row)

Frontend
- Modify: `frontend/src/features/compliance-documents/schemas/compliance-documents-response-schemas.ts`
- Modify: `frontend/src/features/compliance-documents/types/compliance-documents-dto.ts` (`SAFETY_DOMAINS`)
- Modify: `frontend/src/features/compliance-documents/utils/status.ts` (label)
- Modify: `frontend/src/features/compliance-documents/compliance-document-status.test.ts` (label test; schema rejects `labour`)

Docs
- Modify: `docs/architecture/ComplianceDocumentPersistence.md` (P6)
- Modify: `docs/tasks/TASK-P11-012-document-shelf.md` (status line: phase 1 done, after merge)

---

### Task 1: Domain enum and API schema

- [x] Write `tests/domain/test_compliance_enums.py`: values set equals the new list; `SafetyDomain("transport_security")` works; `SafetyDomain("labour")` raises `ValueError`. Update `tests/domain/test_document_type.py`. Run — fails.
- [x] Replace `LABOUR` with `TRANSPORT_SECURITY = "transport_security"` (P1); update `SafetyDomainValue` and the model tuple.
- [x] API tests: `GET /compliance-documents?safety_domain=labour` → 422; `?safety_domain=transport_security` → 200; a document type with `TRANSPORT_SECURITY` serializes as `"transport_security"`.
- [x] `python -m pytest tests/domain tests/api -q`, `python -m ruff check .`.

### Task 2: Migration `0014_transport_security_domain`

- [x] Module test (no DB): revision ids, callables.
- [x] `-m db` test: `downgrade` to `0013`, insert organization + `document_types` row with `safety_domain='labour'`, `upgrade` to `0014` → row is `transport_security`; inserting `labour` violates `ck_document_types_safety_domain`; `downgrade` to `0013` → row is `labour` again and `transport_security` is rejected; upgrade back to head.
- [x] Implement the migration (P2).
- [x] Local: `docker compose up -d`, `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`; `SAFETYMAIN_RUN_DB_TESTS=1 python -m pytest -m db`.

### Task 3: Frontend

- [x] Vitest: `safetyDomainLabel("transport_security")` = «Транспортная безопасность»; response schema parses `transport_security`, rejects `labour`. Run — fails.
- [x] Update zod enum, `SAFETY_DOMAINS`, `SAFETY_DOMAIN_LABELS` (P1). TypeScript `Record<SafetyDomain, string>` forces the label map to be complete.
- [x] `cd frontend && npm run verify`.

### Task 4: Docs and self-review

- [x] P6 line in `ComplianceDocumentPersistence.md`; TASK status line.
- [x] `git grep -n labour -- backend frontend/src tests scripts` returns nothing (migrations excluded by P4).
- [x] Phase 5 checklist of `DevelopmentWorkflow.md`; `CLAUDE.md` / `AI_CONTEXT.md` need no change (no new commands or structure).
- [x] PR: closes acceptance criterion 1; verification output attached.

## Verification

- `python -m ruff check .`
- `python -m pytest`
- `SAFETYMAIN_RUN_DB_TESTS=1 DATABASE_URL=... python -m pytest -m db` (compose Postgres)
- `python -m alembic upgrade head && python -m alembic downgrade -1 && python -m alembic upgrade head`
- `cd frontend && npm run verify`

## Risks

| Risk | Mitigation |
|---|---|
| A production database already has a `labour` document type | Migration converts it; nothing seeds `labour`, so expected count is 0. |
| Users with a bookmarked `?safetyDomain=labour` URL | `parseEnum` drops unknown values to "any domain"; no error. |
| Downgrade after real transport-security types are created | Downgrade maps them back to `labour`, so no row violates the 0013 constraint. |

## Open questions

- **Q1.** TASK §1.4 asks to fix the wording in `SafetyMAIN_Compliance_Documents_Plan.md`. The file is not in the repository or in `~/Documents`, `~/Downloads`, `~/Desktop`. Is it your external document (you fix it yourself), or should it be found and edited?
