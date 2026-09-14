# TASK-P11-000 — Architecture Decisions for Compliance Documentation

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: —

---

## Goal

Record the architecture decisions that the P11 epic relies on, so that every
following task plans against approved ADRs instead of re-deciding
infrastructure in the middle of implementation. This task produces
documentation only. No application code.

---

## Context

Investigated before writing this task:

- `docs/architecture/ADR-0001…ADR-0005` — Entity-Centric, Knowledge Object,
  Metadata Engine, Compliance Rules Engine, Obligations Engine. ADR-0005
  states that reminder mechanisms must be implementations of the Obligations
  Engine. ADR-0004 lists "scheduled evaluation" and "date expiration" as rule
  triggers. Both are conceptual and have no implementation yet.
- `backend/core/infrastructure/storage/`, `messaging/`, `ai/` — empty
  packages. No S3 client, no scheduler, no email, no LLM client anywhere.
  `pyproject.toml` has no such dependencies.
- `docs/domain/SafetyDomainFoundation.md` §12 — "Person masters
  (Employee/Contractor/Visitor) deferred".
- `docs/architecture/SystemLandscape.md` lists Workers, Object Storage, Redis,
  Search as planned infrastructure.
- `docs/architecture/AuditEventIntegrity.md` — hash-chained audit log; reused
  as the integrity mechanism for journals.
- `infrastructure/production/compose.yml` — application-only stack (backend +
  frontend), PostgreSQL on a separate server.
- The repository root contains a stale nested clone `SafetyMAIN/SafetyMAIN/`
  (one commit behind, untracked). It confuses agents that scan the tree.

---

## Scope

### 1. ADR-0006 — Document and Evidence Storage

Decide:

- S3-compatible object storage is the only file store. MinIO in
  `docker-compose.yml` for development; Yandex Object Storage in production
  (same provider `hr_form` already uses).
- Files are uploaded and downloaded through **presigned URLs**; bytes never
  pass through the API container.
- The database stores only metadata: bucket, key, size, MIME type, SHA-256,
  uploaded-by, uploaded-at.
- A port `StorageContract` lives in `backend/core/contracts/`; the boto3
  adapter lives in `backend/core/infrastructure/storage/`. Domain and
  application layers never import boto3 (enforce via the existing
  architecture tests).
- **External references**: a document may point at an object in a bucket
  SafetyMAIN does not own (`complex-hr-docs`). Such objects are read-only,
  never copied, and fetched with a dedicated read-only credential.
- Key scheme for SafetyMAIN-owned objects:
  `{organization_id}/{aggregate}/{aggregate_id}/{version}/{filename}`.
- Retention: objects referenced by an `archived` document are kept; physical
  deletion is out of scope (matches the "no destructive DELETE" rule).

### 2. ADR-0007 — Background Worker and Scheduling

Decide:

- A second process, `safetymain-worker`, built from the same backend image,
  started with a different command. It shares settings, container wiring
  (`AppContainer`), and the Unit-of-Work.
- Job persistence: a PostgreSQL table `scheduled_jobs` (id, kind, payload,
  run_at, locked_at, locked_by, attempts, last_error, status) consumed with
  `SELECT … FOR UPDATE SKIP LOCKED`. No Redis, no Celery for now; document
  the migration path to a broker if throughput ever requires it.
- Recurring schedules are declared in code (a registry of `kind → cron`) and
  materialised into `scheduled_jobs` rows by a scheduler loop; a run is
  idempotent and safe to repeat.
- Job kinds foreseen by P11: `evaluate_obligations` (daily),
  `dispatch_notifications` (every N minutes), `sync_hr` (hourly),
  `process_document_ai` (on demand), `watch_regulations` (daily).
- Every job run is recorded (start, end, outcome, error) for operators; job
  failures never break API requests.
- Production compose gains a `worker` service; the health check is
  "last successful scheduler tick < 5 min ago".

### 3. ADR-0008 — HR Integration Contract

Decide:

- `hr_form` owns employee master data. SafetyMAIN keeps a **read-model**
  `Employee` keyed by `hr_form` `submission_id` (`external_ref`).
- **v1 (read-only)**: `hr_form` publishes a PostgreSQL view
  `hr.safetymain_employees_v` and `hr.safetymain_employee_documents_v` with a
  fixed column list (full name parts, position, department, manager
  reference, hire date, employment status, document `field_key`, storage
  bucket/key, OCR-extracted `issue_date` / `expiry_date` / `number`,
  medical `exam_date` / `next_exam_date` / `decision`). SafetyMAIN connects
  with a role that has `SELECT` on those views only. Personal identifiers are
  **not** in the views.
- The view definition is versioned in `hr_form` (`docs/sql/013_safetymain_views.sql`)
  and mirrored as a contract test fixture in SafetyMAIN that fails when the
  column set changes.
- **v2 (push)**: `POST /api/v1/integrations/hr/events` with an integration
  token (not a user JWT), idempotent by `event_id`; event types `hired`,
  `transferred`, `dismissed`, `manager_changed`. v1 sync remains as
  reconciliation.
- Files from `hr_form` are referenced by bucket/key (ADR-0006 external
  references).

### 4. ADR-0009 — Knowledge Blocks and Document Assembly

Decide:

- An instruction is an **assembly of reusable Knowledge Blocks**, not a
  monolithic text. `KnowledgeBlock` is a Knowledge Object with text
  (Markdown), section kind, safety domain, provenance (source document +
  page, or regulation + clause), version, curation status, and applicability
  tags (asset type, role/position, process/work type, hazard factor,
  regulation).
- `DocumentTemplate` defines the mandatory structure per document type (for an
  instruction: general requirements / before work / during work / emergencies
  / after work / responsibility).
- `DocumentAssembly` = template + ordered list of **block versions** +
  parameters + author edits; generating it produces a `ComplianceDocument`
  version. Assemblies keep block-version references so that a block change
  can find every affected document.
- LLM usage is **Human in the Loop** at every step: classification,
  segmentation, tagging, deduplication proposals, and drafted blocks are
  all `draft` until a curator confirms; only confirmed blocks enter assemblies.
- Ports: `AIProviderContract` (chat completion, structured output) and
  `EmbeddingProviderContract` in `backend/core/contracts/`; adapters in
  `infrastructure/ai/` — `OpenAICompatibleChatProvider` (base URL, key, model
  from settings; used with OpenCode Zen) and `OpenAICompatibleEmbeddingProvider`
  (used with Z.ai). Model name and embedding dimension are settings; the
  dimension is frozen in the pgvector migration.
- Prompt templates are versioned files in the repository; every AI call is
  logged with prompt version, model, token usage, and the produced object id.
- Free-tier gateway models are not allowed for internal documents.

### 5. ADR-0010 — Electronic Journals and Simple Electronic Signature

Decide:

- A journal is an **append-only** register: `Journal` (type, organisation
  unit, responsible, period, status) and `JournalEntry` (schema-driven
  fields, subjects, author, created_at). Entries are never updated or
  deleted; corrections are new entries of kind `reversal` referencing the
  corrected entry.
- Each entry is hashed into the existing audit hash chain
  (`AuditEventIntegrity.md`) so tampering is detectable with the existing
  verification script.
- Entry field schemas are metadata (`JournalType` catalog, ADR-0003), not
  code.
- **Simple electronic signature (ПЭП)**: an entry that requires the employee's
  signature stays `awaiting_signature` until the employee confirms it from
  their own authenticated session. The signature record stores user id,
  timestamp, client IP, user agent, and the SHA-256 of the canonical entry
  payload. Legal basis: an internal regulation on electronic document flow
  that every employee acknowledges (itself a `ComplianceDocument` produced by
  P11-003). Enhanced/qualified signatures are out of scope.
- Employees receive a minimal SafetyMAIN role (`employee`) that can see and
  sign their own entries and acknowledgements only.
- Printable forms mandated by regulation are generated artifacts of the
  electronic register (ADR-0001: documents are generated evidence).

### 6. Documentation updates

- `docs/domain/SafetyDomainFoundation.md` §12: remove "Person masters
  deferred"; reference ADR-0008.
- `docs/architecture/SystemLandscape.md`: mark Workers, Object Storage, AI
  Services as "decided, see ADR-0006/0007/0009"; note that Redis is not
  required for the P11 scope.
- `docs/architecture/README` or index (if one exists) lists the new ADRs.
- `CLAUDE.md`: add the P11 epic to the key documentation map and the
  worker/MinIO commands placeholder (to be completed by P11-001/P11-006).

### 7. Repository hygiene

- Remove the nested stale clone `SafetyMAIN/SafetyMAIN/` (untracked; confirm
  with `git status` that nothing inside it is tracked before deletion).
- Add `SafetyMAIN/` to `.gitignore` is **not** acceptable — delete instead.

---

## Acceptance Criteria

- Five ADR files exist under `docs/architecture/` with the numbering above,
  each with Status, Date, Context, Decision, Consequences, Related ADRs
  sections, matching the style of ADR-0005.
- Every decision listed in Scope §1–§5 is present in the corresponding ADR;
  no decision contradicts ADR-0001…0005.
- Domain foundation and system landscape documents are updated.
- The stale nested clone is gone; `git status` shows only intended changes.
- No application code, migrations, or dependencies were added.

---

## Non-Goals

- Any implementation.
- Choosing specific LLM model names (settings, decided per task in P11-002).
- Enhanced or qualified electronic signatures.
- Message broker selection.

---

## Verification

- Markdown lint / link check as used in the repository (if any).
- Manual review by the product owner (Phase 3 Plan Review applies to the ADR
  texts themselves).
