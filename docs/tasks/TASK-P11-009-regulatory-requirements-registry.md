# TASK-P11-009 — Regulatory Requirements Registry and Gap Analysis

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-006 (obligations), TASK-P11-003 (organisation profile seed)

---

## Goal

Answer the question "which local acts, regulations, instructions, journals,
appointments, and recurring activities must our organisation have under
current legislation?" — as data, traceable to the clause of the regulation
that requires it — and compare that with what SafetyMAIN actually holds.
Gaps become `develop_document` / `review_document` obligations.

This is the top layer of the compliance model (ADR-0004 rules over
ADR-0005 obligations) and is curated by the occupational-safety specialist
and the product owner.

---

## Context

- The organisation profile: ОПО (hazardous production facilities of several
  classes), own transport, dangerous-goods transport, blasting works, and
  more — so all seven safety domains apply.
- `organization_profile` was seeded in P11-003 for document requisites;
  extend it, do not replace it.
- Applicability rules and obligations exist (P11-006). Requirements produce
  obligations through the same engine with `origin=gap_analysis`.
- Sources: pravo.gov.ru (official texts); Garant (lawyer's subscription,
  API to be confirmed). Automated monitoring is P11-010; this task is the
  registry and manual/seeded content.
- Legal accuracy is the curator's responsibility; the system provides
  traceability and workflow, not legal interpretation.

---

## Scope

### 1. Organisation compliance profile

Extend `organization_profile` with structured facts used by applicability:
OKVED codes, hazardous production facilities (registry number, class, type),
vehicle fleet (categories, dangerous-goods flag), blasting works flag,
headcount band, departments, hazard-factor summary (from
`tag_vocabulary` / position profiles), licences held. Admin form + API
(`GET/PATCH /api/v1/organization-profile`).

### 2. Regulations and requirements

- `regulations`: id, `kind` (`federal_law | government_decree | ministry_order |
  fnp | gost | internal`), `number`, `title`, `issuer`, `adopted_at`,
  `edition_date`, `status` (`active | amended | repealed`), `source_url`,
  `tracked` (for P11-010).
- `regulatory_requirements` (Knowledge Object): id, org (or system-level
  shared seed), `regulation_id`, `clause`, `text_quote`, `requirement_kind`
  (`local_act | instruction | journal | appointment | periodic_activity |
  training | medical | report`), `required_document_type_code` (nullable),
  `required_journal_type_code` (nullable), `periodicity_months` (for
  activities/reports, e.g. production-control report by 1 April yearly →
  `due_rule`), `safety_domain`, `status`, `version`, `curator_notes`,
  `ai_summary` (nullable).
- `requirement_applicability` reuses `applicability_rules` with
  `target_kind=regulatory_requirement` and conditions over the organisation
  profile (facility class, fleet, blasting, headcount) and over positions.

### 3. Seed

A curated seed (YAML under `backend/seeds/regulatory/`), reviewed by the
curators before merge, covering at minimum: ТК РФ раздел X; Minlabour
orders 776n (СУОТ), 772n (instructions), 2464 (training/briefings);
116-ФЗ and the relevant ФНП (industrial safety, blasting works); 69-ФЗ,
ПП РФ 1479, МЧС order 806 (fire safety); 7-ФЗ, 89-ФЗ (environment);
196-ФЗ and Mintrans orders (road safety); ПП РФ 272 / ДОПОГ (dangerous
goods); ПП РФ 2168 (production control, annual report). Each entry has
clause, requirement kind, and applicability. Numbers above are to be
verified by the curators during seeding — the task must not hardcode
legal facts the curators have not confirmed.

### 4. Gap analysis

Application service `compute_compliance_gaps()` → for each applicable
requirement: `satisfied` (active document/journal/appointment exists and,
for documents, its `effective_from` ≥ regulation `edition_date` or the
document was reviewed after it), `outdated` (exists but predates the current
edition), `missing`, `not_applicable`. Results are stored per run
(`compliance_gap_runs`, `compliance_gap_items`) and turned into obligations
`develop_document` / `review_document` with `origin=gap_analysis`
(dedupe by requirement). Curators can mark an item `accepted_risk` with
justification (no obligation, audited).

### 5. API

```text
GET/POST/PATCH /api/v1/regulations
GET/POST/PATCH /api/v1/regulatory-requirements ; approve | retire
GET  /api/v1/compliance-gaps           (latest run; filters)
POST /api/v1/compliance-gaps/run       (enqueue)
POST /api/v1/compliance-gaps/items/{id}/accept-risk | reopen
```

Permissions: `regulatory_requirement:read | curate`, `compliance_gap:read |
run | accept_risk`. New role `compliance_curator` mapped to curate/run/
accept plus existing member permissions. Audit: `compliance.requirement.*`,
`compliance.gap.*`.

### 6. Frontend

- Organisation profile form.
- Regulations and requirements registries; requirement object page with
  the quoted clause, applicability, linked document types, and the current
  gap status.
- Gap analysis screen: matrix by safety domain — required / present /
  outdated / missing / accepted risk, drill-down to obligations.

### 7. Documentation

`docs/architecture/RegulatoryRequirements.md`, `docs/api/RegulationsAPI.md`,
`docs/api/ComplianceGapsAPI.md`, seed authoring guide for curators.

---

## Acceptance Criteria

- Profile with an ОПО of class II and dangerous-goods fleet makes the
  corresponding requirements applicable; a profile without them does not
  (table-driven tests).
- Gap run classifies documents correctly against `edition_date`; obligations
  are created once per requirement and closed when a satisfying document is
  activated.
- Curators can approve/retire requirements and accept risks with audit
  trail.
- Seed loads idempotently; the completion report lists which seed entries
  were confirmed by the curators.
- `npm run verify`; E2E: run gap analysis → obligation appears.

---

## Non-Goals

- Automated monitoring of regulation changes (P11-010).
- Legal interpretation by the system; every seeded requirement is
  curator-confirmed.
- Multi-organisation shared seeds beyond a simple system-level flag.

---

## Verification

Unit tests for applicability and gap classification; `db` tests; API tests;
frontend tests; curator review of the seed recorded in the completion report.

---

## Suggested implementation phases

1. Organisation profile extension + API + form.
2. Regulations/requirements model + API + role.
3. Seed loader + curated seed.
4. Gap analysis service + job + obligations.
5. Frontend registries and gap matrix.
