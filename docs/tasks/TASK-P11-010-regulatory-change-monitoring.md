# TASK-P11-010 — Regulatory Change Monitoring with AI Assistance

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-009, TASK-P11-002 (AI ports)

---

## Goal

Keep the regulatory requirements registry current: detect new editions of
tracked regulations, let an LLM compare editions and propose changes to the
affected requirements and the local acts / knowledge blocks that depend on
them, and route every proposal through a curator queue. Nothing in the
registry changes without a human confirmation.

---

## Context

- `regulations.tracked` and `edition_date` exist (P11-009).
- Sources: pravo.gov.ru (official publication; HTML pages, no stable public
  API — fetching and parsing must be tolerant and rate-limited); Garant —
  the lawyer's subscription; whether it includes an API or export is **open**
  (decision pending). Design the source layer as pluggable
  (`RegulationSourceContract`) with a `ManualSource` (curator uploads a new
  edition text/PDF) available from day one, so the feature works even if no
  automated source is usable.
- AI ports and `ai_calls` logging from P11-002; strong model for diffs.
- Knowledge blocks carry `source_regulation_ref`; assemblies carry block
  versions; documents carry `legal_basis` — the impact analysis walks this
  graph.

---

## Scope

### 1. Sources

- `RegulationSourceContract.check(regulation) -> EditionInfo | None` and
  `fetch(edition) -> text`. Implementations: `ManualSource`,
  `PravoGovSource` (best-effort), `GarantSource` (only if API confirmed;
  otherwise a documented stub).
- `regulation_editions`: regulation_id, `edition_date`, `source`, text
  stored in object storage (key), `text_sha256`, `status` (`detected |
  analysed | applied | dismissed`).
- Job `watch_regulations` (daily): for tracked regulations, check sources,
  store new editions, enqueue analysis. Rate limits and polite user agent;
  failures are reported, not retried aggressively.

### 2. AI analysis

- Job `analyse_regulation_change`: diff previous vs new edition text
  (deterministic text diff first), then the strong model summarises the
  changes and, for each affected `regulatory_requirement` (matched by clause
  references and semantic similarity of the quoted clause), proposes:
  `unchanged | amended (new quote, new text) | repealed | new requirement`.
- Impact analysis (deterministic): affected requirements → document types →
  active documents whose `legal_basis` or blocks reference the regulation →
  assemblies → blocks. Result is a `change_proposal` with a tree of impacts.

### 3. Curator queue

- `regulation_change_proposals`: id, edition_id, `summary_md`, `items`
  (JSON of proposed requirement changes), `impacts`, `status`
  (`pending | partially_applied | applied | dismissed`), reviewer, decided_at.
- Applying an item updates the requirement (new version, `edition_date`),
  and creates `review_document` obligations for impacted active documents and
  flags impacted blocks `needs_review` (P11-002 status extension).
- Dismissing requires a reason; everything is audited.

### 4. API and UI

```text
GET  /api/v1/regulation-editions ; POST (manual upload)
GET  /api/v1/regulation-change-proposals ; GET {id}
POST /api/v1/regulation-change-proposals/{id}/items/{n}/apply | dismiss
POST /api/v1/regulations/{id}/check-now
```

Permissions: `regulatory_requirement:curate` (existing). Audit:
`compliance.regulation.edition_detected | proposal_created |
proposal_item_applied | proposal_item_dismissed`.

UI: proposals queue with a diff view (old/new quote), impact tree with links,
apply/dismiss per item; regulation page shows editions timeline and
"проверить сейчас".

### 5. Documentation

`docs/architecture/RegulatoryMonitoring.md`, `docs/api/RegulationChangesAPI.md`,
runbook: source configuration, expected costs, what to do when a source
breaks.

---

## Acceptance Criteria

- A manually uploaded new edition produces a proposal with a summary and
  per-requirement items; applying an item versions the requirement and
  creates review obligations for impacted documents (end-to-end test with
  fake AI).
- No registry change happens without an explicit apply; dismissals are
  audited.
- Source failures are visible in the run report and do not affect other
  jobs.
- All AI calls are logged with cost; the analysis prompt is versioned.
- `npm run verify`; E2E: upload edition → apply item → obligation appears.

---

## Non-Goals

- Guaranteed coverage of every regulation change (automated sources are
  best-effort; the manual path is the guarantee).
- Auto-rewriting knowledge blocks (only flagging for review).
- Legal opinion generation.

---

## Verification

Unit tests for diff and impact walk; job tests with fixtures; API tests;
frontend tests; a documented manual run on one real regulation change.

---

## Suggested implementation phases

1. Source contract + manual source + editions storage + watch job.
2. Diff + AI analysis job + proposals model.
3. Impact analysis + apply/dismiss + obligations.
4. API + UI + docs.
5. Optional: pravo.gov.ru / Garant adapters once access is confirmed.
