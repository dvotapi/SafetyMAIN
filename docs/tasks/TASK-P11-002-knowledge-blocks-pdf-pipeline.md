# TASK-P11-002 — Knowledge Blocks: LLM Decomposition of Existing Instructions

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-001 (documents + storage), TASK-P11-000 (ADR-0007 worker, ADR-0009)

---

## Goal

Turn the organisation's existing PDF instructions (several dozen files) into
a curated, searchable base of **Knowledge Blocks** — reusable fragments of
normative content tagged by asset, role, process, hazard factor, and
regulation — so that P11-003 can assemble new instructions from them.

The pipeline is AI-assisted and human-confirmed: the LLM proposes document
attributes, block boundaries, and tags; a curator confirms or corrects; only
confirmed blocks become usable.

---

## Context

- ADR-0009 (P11-000) fixes the model and the Human-in-the-Loop rule.
- `backend/core/infrastructure/ai/` is empty. Provider decision: chat via
  OpenCode Zen (`https://opencode.ai/zen/v1/`, OpenAI-compatible
  `/chat/completions`), embeddings via Z.ai. Both adapters are OpenAI-compatible
  HTTP clients; no vendor SDK lock-in.
- The worker process is defined by ADR-0007. If P11-006 has not yet delivered
  the worker runtime, this task delivers the minimal worker loop (job table +
  consumer) and P11-006 extends it — decide in planning; do not build two
  schedulers.
- PDF text extraction: prefer a pure-Python extractor for text-layer PDFs;
  scanned PDFs require OCR (Tesseract with `rus` language in the worker
  image). Decide in planning whether OCR is in scope for this task or a
  documented limitation; the existing PDFs must be checked for text layers
  first.
- `pgvector` is not installed. The production PostgreSQL is on a separate
  server; the extension must be enabled there by the DBA. The migration must
  `CREATE EXTENSION IF NOT EXISTS vector` and fail loudly if unavailable.

### Pilot (before Phase 2 planning is approved)

Run a throw-away script (not committed to `backend/`; `scripts/pilot/` is
acceptable) over 5–7 real instructions with two candidate models: classify,
segment, tag. Review the blocks with the occupational-safety specialist.
Decision recorded in the plan: LLM-driven segmentation vs. heading-based
segmentation with LLM tagging only. Record token cost per document.

---

## Scope

### 1. AI ports and adapters

- `backend/core/contracts/ai.py`:
  `AIProviderContract.complete(prompt: PromptRequest) -> PromptResponse`
  with structured JSON output (schema passed in, validated with Pydantic),
  and `EmbeddingProviderContract.embed(texts: list[str]) -> list[list[float]]`.
- `infrastructure/ai/openai_compatible_chat.py`,
  `infrastructure/ai/openai_compatible_embeddings.py`, `fake_ai.py` for tests
  (deterministic canned responses keyed by prompt id).
- Settings: `AI_CHAT_BASE_URL`, `AI_CHAT_API_KEY`, `AI_CHAT_MODEL_FAST`,
  `AI_CHAT_MODEL_STRONG`, `AI_EMBED_BASE_URL`, `AI_EMBED_API_KEY`,
  `AI_EMBED_MODEL`, `AI_EMBED_DIMENSION`, `AI_REQUEST_TIMEOUT_SECONDS`,
  `AI_MAX_RETRIES`. Production validation: keys required when the pipeline
  is enabled (`AI_PIPELINE_ENABLED`).
- Prompt templates as versioned files: `backend/core/application/ai_prompts/
  {classify_document,segment_blocks,tag_block,dedupe_blocks}.v1.md`.
- `ai_calls` table: id, org, job id, prompt id + version, model, input/output
  tokens, latency, status, produced object refs. Never store the API key;
  store the request payload hash, not the payload, unless
  `AI_STORE_PAYLOADS=true` (dev only).
- Architecture tests: `domain`/`application` never import `httpx`/`openai`.

### 2. Data model

- `knowledge_blocks`: id, organization_id, `text_md`, `section_kind`
  (`general | before_work | during_work | emergency | after_work |
  responsibility | other`), `safety_domain`, `curation_status`
  (`draft | reviewed | approved | deprecated`), `version`,
  `canonical_block_id` (nullable; for duplicates pointing at the canonical
  block), `source_document_id`, `source_page_from/to`, `source_regulation_ref`
  (text), `ai_confidence`, `created_by` (`ai | user`), timestamps.
- `knowledge_block_tags`: block_id, `tag_kind` (`asset_type | role | process |
  hazard_factor | regulation | equipment`), `tag_value` (normalised string),
  `tag_ref_id` (nullable link to a Hazard or future Asset), `confirmed`.
- `knowledge_block_embeddings`: block_id, block_version, model, `embedding
  vector(N)`; HNSW or IVFFlat index, decided in planning.
- Tag vocabulary: `tag_vocabulary` (kind, value, title_ru, aliases[]) seeded
  from `hr_form` `position_profiles` (positions) and `hazard_work_items`
  (hazard factors) — copy the catalog JSON into the repo as seed data, do not
  read hr_form's database in this task.

### 3. Pipeline (worker jobs)

For a `ComplianceDocument` with a file the curator triggers "Разобрать":

1. `extract_text` — text layer (or OCR) → stored per page in
  `document_pages` (document_id, page_no, text, method).
2. `classify_document` (strong model) — proposes document type, domain,
   code, title, issue date, approving order, applicability → written as a
   **proposal** on the document (`ai_proposal` JSON), not applied.
3. `segment_blocks` (fast model, or heading-based per pilot decision) —
   proposes blocks with page ranges and section kinds → `knowledge_blocks`
   rows in `draft`.
4. `tag_blocks` (fast model) — proposes tags against the vocabulary; unknown
   values are proposed as new vocabulary entries.
5. `embed_blocks` — embeddings for draft blocks (needed for dedupe).
6. `propose_duplicates` — cosine similarity above a threshold from settings
   → `duplicate_candidates` (block_a, block_b, score, status).

Each step is a `scheduled_jobs` row; failures are retried with backoff and
surfaced on the document's "Разбор" panel. A document's pipeline state is a
backend field (`ai_pipeline_status`), never inferred by the frontend.

### 4. Curation API

```text
POST /api/v1/compliance-documents/{id}/ai/decompose     (enqueue)
GET  /api/v1/compliance-documents/{id}/ai/status
POST /api/v1/compliance-documents/{id}/ai/apply-proposal (accept classified attrs)
GET  /api/v1/knowledge-blocks       (filters: document, status, section, domain,
                                     tag kind/value, search; semantic=true uses
                                     embeddings of the query)
GET  /api/v1/knowledge-blocks/{id}
PATCH /api/v1/knowledge-blocks/{id} (text, section, tags — creates a new version)
POST /api/v1/knowledge-blocks/{id}/review | approve | deprecate
POST /api/v1/knowledge-blocks/{id}/split   (page/char offsets)
POST /api/v1/knowledge-blocks/merge        (ids[])
GET  /api/v1/knowledge-blocks/duplicates   (candidates queue)
POST /api/v1/knowledge-blocks/duplicates/{id}/resolve (keep_a | keep_b | both)
GET/POST /api/v1/tag-vocabulary
```

Permissions: `knowledge_block:read | curate | approve`; `ai_pipeline:run`.
Audit: `compliance.block.*`, `compliance.ai.job_started | job_completed |
job_failed | proposal_applied`.

### 5. Frontend — curation workspace

- Document object page gains a "Разбор" tab: pipeline status, proposal diff
  (proposed vs. current attributes with "Применить"), block list aligned
  with the PDF page preview (use the storage download URL in an iframe or
  pdf.js — decide in planning, keep it in `components/` if generic).
- Block editor: text (Markdown), section kind, tag chips with vocabulary
  autocomplete, source pages, status actions, split/merge.
- Blocks registry with filters and semantic search box.
- Duplicate queue: side-by-side text, similarity, resolve actions.

### 6. Documentation

- `docs/architecture/KnowledgeBlocks.md` (model, pipeline, prompts
  versioning, cost controls).
- `docs/api/KnowledgeBlocksAPI.md`, `docs/api/AIPipelineAPI.md`.
- `docs/infrastructure/ApplicationServerDeployment.md`: pgvector on the DB
  server, worker service, AI settings.

---

## Acceptance Criteria

- Running "Разобрать" on an uploaded text-layer PDF produces a classification
  proposal and draft blocks with tags within the worker, visible on the UI
  with progress and errors.
- A curator can edit, split, merge, tag, and approve blocks; only `approved`
  blocks are returned by the assembly query used in P11-003
  (`curation_status=approved` filter exists and is tested).
- Semantic search returns blocks ranked by cosine distance; the query
  embedding call is logged in `ai_calls`.
- Duplicate candidates are generated and can be resolved; resolved
  duplicates point to a canonical block.
- No AI call is made from an API request handler; all calls run in the
  worker. Tests use `fake_ai.py`; no network in CI.
- `ai_calls` records token usage for every call; a per-day cost report query
  exists (`scripts/ai_usage_report.py`).
- All existing PDFs of the organisation have been processed at least to the
  draft-blocks stage (operational acceptance, tracked in the completion
  report).

---

## Non-Goals

- Assembling new documents (P11-003).
- Automatic application of AI proposals without confirmation.
- Fine-tuning or hosting models.
- Processing hr_form employee documents.

---

## Verification

- Unit tests for prompt/response parsing with recorded fixtures; contract
  tests for the two adapters against a local OpenAI-compatible stub.
- `pytest -m db` for pgvector migration and similarity queries.
- Frontend component tests for the block editor; one E2E for
  decompose → approve block.
- Manual pilot report attached to the completion report (models compared,
  cost per document, curator feedback).

---

## Suggested implementation phases

1. AI ports, adapters, settings, `ai_calls`, prompts, fake provider, tests.
2. pgvector migration, block/tag/vocabulary tables, repositories, seeds.
3. Worker jobs: extract → classify → segment → tag → embed → duplicates.
4. Curation API + RBAC + audit + docs.
5. Frontend curation workspace + tests.
6. Operational run over all existing PDFs; completion report.
