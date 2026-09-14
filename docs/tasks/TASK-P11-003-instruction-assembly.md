# TASK-P11-003 — Instruction Assembly from Knowledge Blocks

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-002

---

## Goal

Let a safety specialist produce a new instruction, regulation, or briefing
program for a specific asset, role, and set of processes by assembling
approved Knowledge Blocks into a document template, filling gaps with
AI-drafted blocks that are clearly marked and must be confirmed, and
generating the final DOCX/PDF as a versioned `ComplianceDocument`.

This closes the business priority "all instructions in electronic form": the
existing PDFs were decomposed in P11-002; from here on documents are produced
from knowledge, not typed from scratch.

---

## Context

- ADR-0009 defines `DocumentTemplate` and `DocumentAssembly`.
- `ComplianceDocument` lifecycle and file attachment come from P11-001; a
  generated file goes through the same `confirm` path (server-side upload in
  the worker instead of a client presigned PUT — extend `StorageContract`
  with `put_object` for worker use).
- Mandatory structure of an occupational-safety instruction (general
  requirements; before work; during work; emergencies; after work) is fixed
  by regulation (Minlabour order 772n). Templates must be data, not code.
- DOCX generation: choose a Python library in planning (`python-docx` or a
  template engine such as `docxtpl`); PDF via LibreOffice headless in the
  worker image or a pure-Python renderer — decide in planning; LibreOffice is
  acceptable in the worker image only.
- Organisation requisites (legal name, logo, signer titles) are needed for
  the title page: add an `organization_profile` settings record (this is
  also the seed of `OrganizationComplianceProfile` in P11-009 — design the
  table so P11-009 extends rather than replaces it).

---

## Scope

### 1. Templates

- `document_templates`: id, org, `document_type_id`, `title`, `version`,
  `status`, `sections` (JSON: ordered list of `{slot_code, title_ru,
  section_kind, required, min_blocks, selection_rules}`), `layout`
  (title page fields, numbering, header/footer), `docx_template_key`
  (storage key of a `.docx` layout with placeholders).
- Seed templates: instruction by profession, instruction by work type,
  briefing program, regulation (generic), order (generic), acknowledgement
  sheet (used by P11-006), journal printable forms (used by P11-005).
- `GET/POST/PATCH /api/v1/document-templates` (admin only for write).

### 2. Assembly

- `document_assemblies`: id, org, template_id + version, `parameters`
  (JSON: asset refs/labels, role/position codes, process codes, hazard
  factor codes, free-text context), `status` (`draft | ready | generated`),
  `result_document_id`, timestamps.
- `document_assembly_items`: assembly_id, slot_code, order, `block_id`,
  `block_version`, `origin` (`selected | suggested | ai_drafted | manual`),
  `text_override_md` (author edits kept separately from the block),
  `confirmed`.
- Selection service (application layer, deterministic):
  for each template slot, candidate blocks = approved blocks matching tags
  (all of role/process/asset when present, weighted), plus top-k semantic
  matches on the slot title + parameters; returns candidates with a score and
  the reason (`tag_match`, `semantic`). No auto-inclusion; the author picks.
- Gap detection: slots with `required=true` and no confirmed items are
  reported as gaps with the missing tag combination.
- AI drafting (worker job `draft_block`): for a gap, the strong model drafts a
  block from the parameters and neighbouring confirmed blocks; result is a
  `KnowledgeBlock` in `draft` with `created_by=ai`, attached to the assembly
  as `ai_drafted`, visibly marked until the curator approves the block.
- Assemblies referencing a block version that is later superseded are
  flagged (`stale_items` computed field) — used by P11-006 to raise a
  review obligation.

### 3. Generation

- Worker job `generate_document`: renders Markdown of confirmed items into
  the DOCX layout, adds title page and requisites, computes the table of
  contents, converts to PDF, uploads both, and creates (or versions) the
  `ComplianceDocument` in `draft` with `source=generated`,
  `assembly_id` back-reference, and `applicability` derived from parameters.
- Regeneration of an existing document creates a new document version and
  keeps the assembly link.
- Rendering is deterministic: the same assembly renders byte-identical
  Markdown (DOCX binary may differ in metadata; test on the intermediate
  Markdown).

### 4. API

```text
POST /api/v1/document-assemblies
GET  /api/v1/document-assemblies/{id}          (with items, candidates, gaps)
PATCH /api/v1/document-assemblies/{id}         (parameters)
POST /api/v1/document-assemblies/{id}/suggest  (recompute candidates)
POST /api/v1/document-assemblies/{id}/items    (add block to slot)
PATCH/DELETE-like archive for items (reorder, override text, confirm, remove)
POST /api/v1/document-assemblies/{id}/draft-gap {slot_code}   (enqueue AI draft)
POST /api/v1/document-assemblies/{id}/generate               (enqueue)
GET  /api/v1/document-assemblies/{id}/preview   (rendered Markdown → HTML)
```

Permissions: `document_assembly:read | edit | generate`; drafting also
requires `ai_pipeline:run`. Audit: `compliance.assembly.*`.

### 5. Frontend — assembly workspace

- Wizard: template → parameters (positions and processes from vocabulary,
  assets free text until an Asset registry exists) → slots.
- Slot editor: left column candidates (score, reason, source document),
  right column chosen items with drag-reorder, inline override editor,
  "AI черновик" button on gaps with a prominent "сгенерировано, требует
  проверки" state.
- Preview pane (HTML from `/preview`); "Сформировать документ" → progress →
  link to the resulting `ComplianceDocument` (which then follows the P11-001
  approve/activate flow).
- Block detail side drawer reused from P11-002.

### 6. First real deliverable

Use the feature to produce the **Regulation on electronic document flow and
simple electronic signature** required by ADR-0010 and P11-005, and at least
one instruction by profession. Record both in the completion report.

---

## Acceptance Criteria

- An author can create an assembly, get ranked candidates per slot, add and
  reorder blocks, override text, see gaps, request an AI draft that appears
  clearly marked, and generate DOCX + PDF that lands as a `draft`
  `ComplianceDocument` with files in storage.
- Generation is a worker job; API requests never render documents inline.
- Only `approved` blocks are offered as candidates; `ai_drafted` items block
  generation until their block is approved.
- Assemblies track block versions; a test proves `stale_items` is reported
  after a block is edited.
- Templates are data; adding a new section to the instruction template
  requires no code change (covered by a test that renders a modified
  template).
- Frontend `npm run verify` passes; E2E covers wizard → generate.

---

## Non-Goals

- Approval workflow with multiple signers (single approve action from
  P11-001 is enough for now).
- Automatic regeneration when blocks change (only flagging).
- Editing DOCX layouts in the UI (layouts are uploaded files).
- Asset registry.

---

## Verification

- Unit tests: selection scoring, gap detection, Markdown rendering snapshots.
- Worker tests with fake AI and in-memory storage.
- `pytest -m db`, `ruff`, frontend `verify`.
- Manual: generated DOCX opens in Word/LibreOffice with correct Cyrillic
  fonts, numbering, and table of contents.

---

## Suggested implementation phases

1. Templates model + seeds + API.
2. Assembly model + selection service + gap detection + API.
3. AI drafting job + marking rules.
4. Rendering + generation job + storage `put_object` + document creation.
5. Frontend workspace + tests + E2E.
6. Produce the e-signature regulation and one instruction; completion report.
