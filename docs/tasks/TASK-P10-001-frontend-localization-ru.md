# TASK-P10-001 — Full Russian Localization (Frontend, Single Language)

> Naming note: no prior task in this phase range exists. This task is filed as
> `P10-001` because it is the first horizontal, cross-cutting frontend task
> after the `P9` vertical-slice sequence (`P9-001`..`P9-007c`). Rename during
> Phase 1 review if a different numbering convention is preferred.

---

## Goal

Replace all user-facing text in the SafetyMAIN frontend with Russian, as a
**single fixed language** — no language switcher, no runtime locale
negotiation.

Scope is frontend-only. The backend (API responses, audit taxonomy, domain
enum wire values, emails if any) is explicitly out of scope and stays in
English.

"User-facing text" includes both:

- **Static copy** — literal strings in JSX/TSX: labels, buttons, headings,
  table columns, form fields, tooltips, empty states, dialogs, navigation,
  page titles, accessibility text (`aria-label`, `alt`), the `<html lang>`
  attribute, and the error/loading/not-found/forbidden/unauthorized/
  session-expired/login pages.
- **Generated/computed copy** — text assembled at runtime rather than typed
  literally: toast and inline error messages, backend-error-to-user-message
  mapping, enum-to-label mapping (status/lifecycle/severity/effectiveness
  labels), formatted dates and numbers, and any string that interpolates a
  count (list counts, "N of M" pagination text, etc.).

Both categories must render in Russian. This is the "generated content must
also be Russian" requirement — it does not refer to a document/PDF export
feature, because none exists in the frontend today (confirmed by
investigation, see Known Limitations).

---

## Context

Investigated before writing this task:

- `AI_CONTEXT.md`, `docs/ai/DevelopmentWorkflow.md`.
- `docs/tasks/TASK-P9-002.md` and `docs/architecture/frontend/SharedUIComponents.md`
  — both explicitly defer i18n: _"i18n, offline, production observability —
  later tasks."_ No i18n library, locale routing, or translation-key
  infrastructure exists anywhere in `frontend/`.
- `frontend/package.json` — no `next-intl`, `react-intl`, `i18next`, or
  similar dependency installed.
- `frontend/src/app/layout.tsx` — `<html lang="en">`, `metadata.title =
"SafetyMAIN"`, `metadata.description` in English. Fonts (`IBM_Plex_Sans`,
  `IBM_Plex_Mono`) already load the `cyrillic` subset, so no font change is
  needed.
- `frontend/src/utils/format-date.ts` — `formatDateOnly` / `formatDateTime`
  use `Intl.DateTimeFormat(undefined, …)`, i.e. the browser's default locale,
  not a fixed one. Must become explicit `"ru-RU"`.
- `frontend/src/services/api/errors.ts` — `toUserSafeMessage()` is the single
  centralized function that turns `ApiClientError` kinds into user-facing
  strings (network / authentication / permission / not_found / conflict /
  tenant_context / validation / default). All six generic branches are
  hardcoded English literals in one place — good, single translation point.
  The `validation` branch falls back to `error.message`, which for some
  backend-originated validation errors passes backend-authored English text
  through verbatim (see Known Limitations).
- `frontend/src/lib/navigation.ts` — full current nav tree: `Overview`,
  `Safety` (`Hazards`, `Risk Assessments`, `Risk Controls`), `People`,
  `Knowledge`, `Analytics`, `Administration`.
- `frontend/src/components/patterns/PlaceholderSectionPage.tsx` — used by
  `People`, `Knowledge`, `Analytics`, `Administration` routes (no business UI
  yet, per `TASK-P9-002`/`SharedUIComponents.md`). Placeholder copy is still
  user-visible and must be translated even though the underlying feature is
  deferred.
- Three production-connected feature verticals exist today: `hazards`,
  `risk-assessments`, `risk-controls` (`frontend/src/features/*`), plus
  `auth` (login, session handling) and the shared design system in
  `frontend/src/components/`, `frontend/src/layouts/`.
- Repository-wide count: 186 `.tsx` files under `frontend/src` (excluding
  `node_modules`/`.next`), all currently English.
- No PDF/CSV/print/export generation exists in the frontend (initial grep hit
  was a false positive on the `export` keyword of ES module syntax, not a
  feature).

---

## Scope

### 1. Russian domain glossary (produce and lock first)

A single canonical EN→RU glossary must be written and approved before any
component text is changed, so the same backend concept gets the same Russian
term everywhere (a Risk Control screen and a Hazard screen must not invent
two different translations for the same status word).

Minimum terms to cover, derived from existing feature code and `CLAUDE.md`'s
aggregate list:

```text
Navigation:     Overview, Safety, Hazards, Risk Assessments, Risk Controls,
                People, Knowledge, Analytics, Administration

Aggregates:     Hazard, Risk, Risk Assessment, Risk Control, Organization,
                Incident, Inspection, Corrective Action, Training, Permit,
                Emergency Asset, Audit Event

Risk Control lifecycle: Draft, Proposed, Assigned, Planned, In Progress,
                Implemented, Verified, Effective, Partially Effective,
                Ineffective, Overdue, Suspended, Resumed, Superseded,
                Cancelled, Archived

Common actions: Assign owner, Plan implementation, Start implementation,
                Update progress, Add evidence, Complete implementation,
                Verify effectiveness, Schedule review, Complete review,
                Suspend, Resume, Supersede, Cancel, Archive, Materialize

Generic UI:     Draft/Submit/Approve/Reject, Save/Cancel, Create/Edit/Delete,
                Filters, Search, Clear all, Loading, Empty state, No results,
                Showing N of M, Required field, Optional
```

This glossary should be written down as an appendix to the approved
implementation plan (Phase 2) or as a short `docs/design/` reference, not
scattered across PR descriptions.

### 2. Static UI text sweep

Replace every hardcoded English string in:

```text
frontend/src/app/**            (routes, metadata, error/loading/not-found pages)
frontend/src/features/**       (hazards, risk-assessments, risk-controls, auth)
frontend/src/components/**     (shared design system — patterns, forms, dialogs,
                                navigation, feedback, registry, workflow, data-display)
frontend/src/layouts/**
```

Explicitly included:

- `frontend/src/app/layout.tsx`: `lang="ru"`, `metadata.title`,
  `metadata.description`.
- `frontend/src/lib/navigation.ts`: all nav `label` values.
- Every route under `app/` that currently renders literal English copy:
  `error.tsx`, `global-error.tsx`, `not-found.tsx`, `loading.tsx`,
  `login/`, `session-expired/`, `unauthorized/`, `forbidden/`.
- `PlaceholderSectionPage.tsx` copy (`"Placeholder route for navigation
structure. Business UI is deferred to later tasks."` and its `title` prop
  usages in `people`, `knowledge`, `analytics`, `administration` pages).
- Accessibility text: `aria-label`, `aria-describedby`-linked copy, `alt`
  attributes, icon-only button labels — these are real user-facing text for
  screen-reader users and are in scope.

Excluded (see Non-Goals): `*.stories.tsx`, `*.test.tsx`, `e2e/**`, code
comments, identifiers, commit messages.

### 3. Generated/computed text

- `frontend/src/services/api/errors.ts` → `toUserSafeMessage()`: translate
  all six hardcoded generic branches to Russian. Document that the
  `validation` branch's `error.message` fallback may still surface an
  English backend-authored string for some errors — this is a known
  limitation, not a bug to be engineered around on the frontend (see Known
  Limitations).
- Each feature's validation-error mapping (e.g.
  `features/risk-assessments/utils/map-validation-errors.ts` and its
  equivalents in `hazards`/`risk-controls`) must produce Russian field-level
  messages.
- Every enum-to-label mapping (lifecycle status, severity, likelihood,
  effectiveness outcome, review outcome, etc. — e.g.
  `hazard-status.ts`, `risk-assessment-status.ts`, `risk-control-status.ts`,
  `effectiveness-status.ts`) must return Russian labels, using the glossary
  from §1. Backend enum _wire values_ (e.g. `"APPROVED"`) do not change —
  only their frontend display label does.
- `frontend/src/utils/format-date.ts`: switch `Intl.DateTimeFormat(undefined,
…)` to `Intl.DateTimeFormat("ru-RU", …)` in both `formatDateOnly` and
  `formatDateTime`.
- Any string that interpolates a count (list counts, "N selected", "Showing N
  of M", pagination summaries) must use correct Russian plural grammar (1 /
  2–4 / 5–20 &amp; 0 forms differ), via one small shared pluralization helper
  — not ad hoc per call site. This is a plain utility function, not an i18n
  library.

### 4. Tests

Any Vitest/Testing-Library assertion or Playwright selector that currently
matches English copy (`getByText`, `getByRole(..., { name: … })`, snapshot
text) breaks the moment the corresponding UI text changes to Russian. Tests
must be updated in the same implementation phase as the UI they cover — not
deferred to a final pass. Where a test's intent is structural (e.g. "the
submit button exists and is enabled") prefer `getByTestId` / `getByRole`
without a hardcoded English `name` filter, to reduce future churn.

---

## Acceptance Criteria

- [ ] A locked EN→RU glossary exists and is referenced by the implementation.
- [ ] No hardcoded English user-facing string remains in `app/`, `features/*`,
      `components/*`, `layouts/*` (stories/tests excluded).
- [ ] `<html lang="ru">`; page `<title>`/`metadata` in Russian.
- [ ] All navigation labels, all routes (including error/loading/not-found/
      forbidden/unauthorized/session-expired/login/placeholder pages) render
      in Russian.
- [ ] `toUserSafeMessage()` and all per-feature validation-error mappers
      produce Russian text.
- [ ] All status/lifecycle/severity/effectiveness enum labels render in
      Russian and use consistent terminology across Hazards, Risk
      Assessments, and Risk Controls.
- [ ] Dates render with Russian month/weekday names via explicit `"ru-RU"`
      formatting.
- [ ] Count-bearing strings use correct Russian plural forms.
- [ ] `npm run lint`, `npm run typecheck`, `npm run test`, `npm run test:e2e`,
      and `npm run architecture:check` all pass with tests updated to match
      Russian copy.
- [ ] Manual spot check in a running browser (`npm run dev`) of: login,
      Overview, Hazards registry + object page, Risk Assessments registry +
      object page, Risk Controls registry + object page, People/Knowledge/
      Analytics/Administration placeholders, and the error/not-found/
      unauthorized/forbidden/session-expired pages.

---

## Non-Goals

- No language switcher, no `next-intl`/`react-intl`/`i18next`, no locale
  routing, no translation-key/message-catalog infrastructure. Single fixed
  language, per explicit product decision — building a multi-language
  framework for a single-language requirement is out of scope.
- No backend translation: API error messages, audit event taxonomy, domain
  enum wire values, seed/fixture data stay in English.
- No translation of `*.stories.tsx` (Storybook is internal developer
  tooling, not user-facing).
- No new document/export/PDF/print generation feature — none exists today;
  this task does not add one.
- No change to API contracts, DTOs, permission names, or enum wire values —
  only frontend display labels change.
- No component redesign or layout changes — this is a copy and
  locale-formatting change, not a visual refactor.

---

## Verification

- `npm run lint` (`--max-warnings=0`)
- `npm run typecheck`
- `npm run test` (Vitest, assertions updated to Russian copy)
- `npm run test:e2e` (Playwright, selectors/assertions updated)
- `npm run architecture:check` (dependency-cruiser — must stay clean; this
  task should not need new cross-boundary imports)
- Manual browser walkthrough of the pages listed in Acceptance Criteria
- Post-implementation residual-English sweep: grep the touched directories
  for common leftover English UI words to catch missed strings

---

## Risks

- **Coverage risk** — 186 files is a large surface; strings are easy to miss
  in less-visited states (empty states, rare error branches, dialog
  confirmations). Mitigate with a final grep sweep, not just visual
  spot-checking.
- **Terminology drift** — same English term translated two different ways in
  two features if the glossary (§1) isn't produced and enforced first.
- **Test brittleness** — text-based test selectors will break in bulk;
  budget real time for this, don't treat it as incidental.
- **Partial backend leakage** — `toUserSafeMessage()`'s `validation` branch
  can still surface a raw English `error.message` from the backend for some
  error responses. This cannot be fixed on the frontend without inventing
  backend behavior, which `CLAUDE.md` forbids. Documented as a known
  limitation, not solved by this task.
- **Missed enum values** — every backend-defined enum consumed by a status/
  label mapper must be inventoried per aggregate (Hazard, Risk Assessment,
  Risk Control today; Incident/Inspection/Corrective Action/Training/Permit/
  Emergency Asset if/when their UI ships) during Phase 2 planning. A missed
  value falls back to raw backend text (e.g. `"APPROVED"`) leaking into an
  otherwise-Russian screen.

---

## Known Limitations

- Backend-authored free-text validation messages passed through
  `error.message` may remain in English; only frontend-owned generic and
  field-level copy is guaranteed Russian.
- Content that does not exist in the frontend today (document export, PDF
  generation, email templates) is not addressed by this task because there
  is nothing to translate; if such a feature is built later, its copy should
  default to Russian per this task's precedent, not per new infrastructure.
- `People`, `Knowledge`, `Analytics`, `Administration` remain placeholder
  pages (per `TASK-P9-002`); this task translates the placeholder copy itself
  but does not build the deferred business UI.

---

## Suggested Implementation Phasing

(For the Phase 2 plan to confirm/adjust — large tasks must not be implemented
in one shot.)

```text
Phase A — Foundations
  Glossary lock-in, pluralization helper, ru-RU date formatting, <html lang>,
  metadata, navigation labels, shared design-system components (patterns,
  forms, dialogs, feedback, registry, workflow, data-display, navigation),
  auth/login, error/loading/not-found/forbidden/unauthorized/session-expired
  pages, toUserSafeMessage().

Phase B — Hazards feature copy + enum labels + tests

Phase C — Risk Assessments feature copy + enum labels + tests

Phase D — Risk Controls feature copy + enum labels + tests

Phase E — Placeholder pages (People/Knowledge/Analytics/Administration),
  residual-English grep sweep, full verification suite
```

Each phase should ship as its own reviewable diff, matching the existing
`P9-007a/b/c` precedent for splitting large frontend work.

---

## Implementation Plan (Phase 2 draft)

Status: Approved  
Date: 2026-08-16  
Current implementation phase: E — Placeholders + residual grep (implemented, ready for review)

### Phase A completion notes

- Glossary locked in `docs/design/RussianUICopy.md`; StatusLanguage RU column added.
- `APP_LOCALE`, `formatDate*` (`ru-RU`), `formatPluralRu`, shared DS / auth / system pages / nav / `toUserSafeMessage` translated.
- Leftover `Intl.DateTimeFormat(undefined)` call sites switched to `APP_LOCALE`.
- Vitest, lint, typecheck, architecture:check, auth+smoke E2E pass after fresh `npm run build`.
- Feature chrome (Hazards / RA / RC) and placeholders remain for Phases B–E.

### Phase B completion notes

- Hazard status/category/source/direction/subject maps; removed `formatHazardEnumLabel`.
- Related RA status/profile/risk-level labels on hazard object page (Phase C owns full RA maps).
- Zod messages, ACTIVITY_TITLES, registry/create/object/forms/lifecycle/activity/conflict translated.
- Vitest hazards, lint, typecheck, architecture:check, `e2e/hazards.spec.ts` pass after fresh build.
- Risk Assessments / Risk Controls / placeholders remain for Phases C–E.

### Phase C completion notes

- RA status/profile/object-type/acceptance/factor/risk-level maps; removed `formatRiskAssessmentEnumLabel`.
- Catalog titles, HoC labels, Zod, approve-acceptance, ACTIVITY_TITLES, pages/components translated.
- Vitest RA (59), lint, typecheck, architecture:check, `e2e/risk-assessments.spec.ts` pass after fresh build.
- Risk Controls + placeholders remain for Phases D–E.

### Phase D completion notes

- RC status/effectiveness/nature/evidence/verification/review/owner/milestone maps; `formatRiskControlEnumLabel` is lookup+raw fallback (no title-casing).
- Zod schemas, ACTIVITY_TITLES, materialize dialog, registry/object/lifecycle chrome translated.
- Vitest RC (171), lint, typecheck, architecture:check, `e2e/risk-controls.spec.ts` (19) pass after fresh build.
- Placeholders + residual grep remain for Phase E.

### Phase E completion notes

- `PlaceholderSectionPage` + people/knowledge/analytics/administration/safety placeholder titles in Russian.
- Residual English chrome grep for common UI phrases: clean (stories / API throws / fixture bodies out of scope).
- Full `npm run verify` PASS (tokens, format, lint, typecheck, architecture, 273 tests, build).
- Full `npm run test:e2e` PASS (34/34).

This section is the Phase 2 implementation plan. It does not replace Goal,
Scope, Acceptance Criteria, Non-Goals, or Verification above.

---

### 1. Goal

Replace every user-facing frontend string with Russian as a **single fixed
language**. No i18n library, no locale routing, no message catalog, no
language switcher.

Backend contracts, enum wire values, API error bodies, and audit event names
stay English. Only frontend display labels, static copy, Zod messages,
generic error strings, dates, and count grammar change.

---

### 2. Approved assumptions

Confirmed by repository evidence unless marked **proposal** (those need
glossary lock in Phase 3).

1. **No i18n framework.** `frontend/package.json` has no `next-intl` /
   `react-intl` / `i18next`. Copy stays hardcoded Russian in the same files
   that hold English today.
2. **Fonts already support Cyrillic.** `layout.tsx` loads
   `IBM_Plex_Sans` / `IBM_Plex_Mono` with `cyrillic`. No font change.
3. **English source of truth for glossary is production UI +
   `docs/design/StatusLanguage.md`, not the approximate lifecycle list in
   this TASK's §1.** Production Risk Control statuses are `draft | planned |
in_implementation | implemented | verified_effective |
verified_ineffective | suspended | superseded | archived | cancelled`.
   TASK terms `Proposed`, `Assigned`, `Resumed` are actions / audit titles,
   not lifecycle statuses. `Overdue` is an overlay (`visualStatusLabels`),
   not a Risk Control status. **Proposal:** lock Appendix A against the
   inventoried enums below.
4. **Shared status chips already exist.**
   `frontend/src/components/primitives/status-types.ts` →
   `visualStatusLabels`. Features also keep their own `STATUS_LABELS`.
   Both must use the same Russian words from Appendix A. Do not add a new
   message-catalog module. Do not import feature label maps into
   `components/`.
5. **`format*EnumLabel` is the main English leak.** Title-casing
   `organizational_unit` → `"Organizational Unit"` is used for Hazard
   category/source/direction/subject, RA profile/object/acceptance/HoC
   factors, RC nature/evidence/verification/review/owner/milestone. Replace
   with explicit `Record<Dto, string>` maps. Unknown wire values fall back
   to the raw backend token (e.g. `organizational_unit`), not title-cased
   English — matches the TASK missed-enum risk note.
6. **Validation mappers do not invent backend translation.**
   - Hazards: no `map-validation-errors.ts`. Zod messages +
     `toUserSafeMessage` + one duplicate-code string on create.
   - RA: `mapRiskAssessmentValidationDetails` maps paths; **messages come
     from the backend body** and may stay English (Known Limitation).
   - RC: `flattenValidationError` in `use-risk-control-command.ts` same
     pattern.
     Frontend-owned Zod / fallback strings become Russian. Do not add a
     Hazard mapper that does not exist. Do not rewrite backend `message`
     text on the client.
7. **Frontend `ACTIVITY_TITLES` maps are in scope.** Non-Goals keep backend
   audit _taxonomy_ (event name wire values) in English. The frontend maps
   those codes to user-visible activity titles in `hazard-api.ts`,
   `risk-assessment-api.ts`, `risk-control-api.ts`. Those titles are
   generated UI copy and must be Russian.
8. **User-authored / fixture data stays as stored.** Hazard titles, evidence
   titles, organization names, emails in E2E fixtures are content, not
   chrome. Do not translate fixture payloads.
9. **Stories stay English** (`*.stories.tsx` Non-Goal). `DemoValidatedForm`
   lives under `components/` and is unused by routes; still translate it in
   Phase A because `components/*` is in Scope §2.
10. **Locale constant is a utility, not a catalog.** One
    `APP_LOCALE = "ru-RU"` plus `formatDate*` and `formatPluralRu`. Six extra
    `Intl.DateTimeFormat(undefined, …)` call sites besides `format-date.ts`
    must also use `"ru-RU"` (or the shared helpers).
11. **Status chip grammar (proposal).** Shared badges use short invariant
    forms from Appendix A (Черновик, Архив, На рассмотрении) — no per-aggregate
    gender agreement. Same string on Hazard, RA, and Risk Control.

---

### 3. Open questions

Must be answered before Phase A implementation. Proposed answers are in
Appendix A / assumptions above.

| #   | Question                                                                                    | Proposed default if approved                                                           |
| --- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Q1  | Lock Appendix A as the canonical EN→RU glossary?                                            | Yes. Write it to `docs/design/RussianUICopy.md` in Phase A.                            |
| Q2  | Risk Control display name: «Мера управления риском» vs «Мера контроля» vs «Контроль риска»? | **Мера управления риском.** Short UI: «Мера». Nav: «Меры управления риском».           |
| Q3  | `materialize` user verb?                                                                    | **Создать меры** (command). Keep wire/command id `materialize`.                        |
| Q4  | Translate frontend `ACTIVITY_TITLES`?                                                       | Yes (assumption 7).                                                                    |
| Q5  | Invent a Hazard 422 mapper?                                                                 | No (assumption 6).                                                                     |
| Q6  | Keep HTTP codes on 401/403 pages (`401 Unauthorized`)?                                      | Translate the sentence; keep the numeric code (`401`, `403`) as a technical reference. |

If any row is rejected, stop and revise Appendix A before coding.

---

### 4. Backend contract

No API, DTO, permission, lifecycle, or enum **wire** changes.

Frontend continues to send/receive existing English tokens:

| Area             | Unchanged wire                                                      | Frontend display only                             |
| ---------------- | ------------------------------------------------------------------- | ------------------------------------------------- |
| Hazard status    | `draft`, `active`, `archived`                                       | Appendix A                                        |
| Hazard enums     | category / source / safety_direction / affected_subject             | Appendix A                                        |
| RA status        | `draft`, `under_review`, `approved`, `superseded`, `archived`       | Appendix A                                        |
| RA enums         | profile, object type, acceptance, HoC, risk level, factors          | Appendix A                                        |
| RC status        | production list in assumption 3                                     | Appendix A                                        |
| RC enums         | nature, evidence, verification, review basis, owner type, milestone | Appendix A                                        |
| Permissions      | `hazard:read`, `risk:read`, `risk_control:read`, …                  | never shown as raw permission strings in UI today |
| Audit            | `event_name` e.g. `safety.hazard.created`                           | `ACTIVITY_TITLES` Russian                         |
| 422 / 409 bodies | English `message` / `violations[].message`                          | pass-through (limitation)                         |

`toUserSafeMessage()` remains the single generic mapping for
`network | authentication | permission | not_found | conflict |
tenant_context | validation-fallback | default`.

---

### 5. Architecture boundaries

Allowed:

```text
app → features → components/layouts → theme/utils/icons
features/*/utils  — feature enum label maps (existing files)
frontend/src/utils/format-date.ts
frontend/src/utils/format-plural.ts   # new, domain-neutral
frontend/src/utils/locale.ts          # new, APP_LOCALE only
docs/design/RussianUICopy.md          # glossary reference
```

Forbidden:

- `next-intl` / `react-intl` / `i18next` / locale routes / JSON catalogs
- `components` → `features`
- feature A importing feature B internals for labels
- shared “t()” or message-id infrastructure
- new endpoints or translated backend payloads
- layout / visual redesign
- translating `*.stories.tsx`, comments, identifiers, MSW fixture content

Reuse:

- Existing `*StatusLabel` / `visualStatusLabels` / `ACTION_LABELS` /
  `ACTIVITY_TITLES` / Zod `message:` sites — replace string values in place
- Existing `toUserSafeMessage`
- Registry pattern pagination slots (copy only)
- `P9-007a/b/c` phase-split precedent

New shared code (justified): Russian plural helper cannot live in a feature
without duplicating 1/2–4/5–20 rules (TASK §3). Locale constant avoids six
divergent `"ru-RU"` literals drifting back to `undefined`.

---

### 6. Affected files

Not an exhaustive 186-file dump. Every file under the trees below that
contains user-facing English is in scope for the named phase. Stories
excluded.

**Phase A — foundations**

- `docs/design/RussianUICopy.md` (new), `docs/design/README.md`,
  `docs/design/StatusLanguage.md` (add RU label column; do not restyle)
- `frontend/src/utils/locale.ts` (new), `format-date.ts`,
  `format-plural.ts` (new) + unit tests
- `frontend/src/app/layout.tsx`, `global-error.tsx`, `error.tsx`,
  `not-found.tsx`, `loading.tsx` (no copy today), `login/page.tsx`,
  `unauthorized/page.tsx`, `forbidden/page.tsx`, `session-expired/page.tsx`,
  `page.tsx` (Overview)
- `frontend/src/lib/navigation.ts`
- `frontend/src/layouts/AppShell.tsx`
- `frontend/src/services/api/errors.ts`
- `frontend/src/components/primitives/status-types.ts`, `StatusBadge.tsx`
  (`aria-label` prefix `Status:` → `Статус:`), `Button.tsx`, `Input.tsx`,
  `Select.tsx`
- `frontend/src/components/feedback/Feedback.tsx`
- `frontend/src/components/filters/Search.tsx`, `ClearAll.tsx`,
  `FilterChip.tsx`
- `frontend/src/components/dialogs/ConfirmationDialogs.tsx`
- `frontend/src/components/data-display/DataTable.tsx`, `Chip.tsx`
- `frontend/src/components/registry/RegistrySelection.tsx`
- `frontend/src/components/timeline/Timeline.tsx`
- `frontend/src/components/navigation/Breadcrumbs.tsx`, `Menus.tsx` (if
  hardcoded chrome), `AppShell` already owns Sign out
- `frontend/src/components/object-page/ObjectTabs.tsx`, `ObjectSidebar.tsx`
- `frontend/src/components/workflow/WorkflowStepper.tsx`
- `frontend/src/components/patterns/DemoValidatedForm.tsx`
- `frontend/src/features/auth/LoginForm.tsx`, `AuthShellGate.tsx`
- Tests: `src/test/bootstrap.test.tsx`, `DataTable.test.tsx`,
  `FilterChip.test.tsx`, Timeline/Workflow tests if they assert chrome
- E2E login chrome in **all** specs: `e2e/auth.spec.ts`, `smoke.spec.ts`,
  `hazards.spec.ts`, `risk-assessments.spec.ts`, `risk-controls.spec.ts`
  (shared `Sign in` / `Email` / `Password` / `Overview` / `Sign out`)

**Phase A also switches remaining `Intl.DateTimeFormat(undefined)`** in
feature files to `APP_LOCALE` / shared helpers so dates do not stay
browser-locale after foundations. That is locale plumbing, not feature copy.

**Phase B — Hazards**

- `features/hazards/utils/hazard-status.ts` (status map + replace
  `formatHazardEnumLabel` with category/source/direction/subject maps)
- `schemas/hazard-form-schema.ts` (Zod messages)
- `api/hazard-api.ts` (`ACTIVITY_TITLES`)
- `pages/*`, `components/*` (forms, registry, object, activity, related)
- `hazard.test.ts`, `hazard-related-assessments.test.tsx`
- `e2e/hazards.spec.ts` (remaining chrome; login already Phase A)

**Phase C — Risk Assessments**

- `utils/risk-assessment-status.ts`, `hierarchy-of-controls.ts`,
  `assessment-profiles.ts` (titles)
- New or extended explicit maps for object type, acceptance, factors
- `schemas/risk-assessment-form-schema.ts`, `utils/map-validation-errors.ts`
  (only fallbackMessage / frontend-owned strings)
- `api/risk-assessment-api.ts` (`ACTIVITY_TITLES`)
- `pages/*`, `components/*`
- `*.test.ts(x)` that assert copy
- `e2e/risk-assessments.spec.ts`

**Phase D — Risk Controls**

- `utils/risk-control-status.ts` (status, effectiveness, implementation
  state; replace `formatRiskControlEnumLabel`)
- All `schemas/*.ts` Zod messages
- `api/risk-control-api.ts` (`ACTIVITY_TITLES`)
- `hooks/use-risk-control-command.ts` (flatten fallback only)
- `pages/*`, `components/*` (command dialogs, materialize, lifecycle)
- `risk-control-*.test.ts(x)`, `materialization.test.tsx`
- `e2e/risk-controls.spec.ts` (including `Mar 1, 2027` → `ru-RU` medium date)

**Phase E**

- `components/patterns/PlaceholderSectionPage.tsx`
- `app/people/page.tsx`, `knowledge/page.tsx`, `analytics/page.tsx`,
  `administration/page.tsx`, `app/safety/page.tsx` if it has chrome
- Residual grep + full `lint` / `typecheck` / `test` / `test:e2e` /
  `architecture:check`
- Manual walkthrough from Acceptance Criteria

Out of scope files: `*.stories.tsx`, comments, `features/*/api` throw
messages that never reach UI (`Empty login response` etc.), MSW/E2E
JSON bodies.

---

### 7. Implementation phases

Each phase is one reviewable diff. Do not start the next phase without
explicit approval. Do not mix feature copy into Phase A except date-locale
plumbing and E2E login selectors.

#### Phase A — Foundations

**Scope**

- Lock glossary: add `docs/design/RussianUICopy.md` from Appendix A;
  link from `docs/design/README.md`; add RU column to StatusLanguage.md
- `APP_LOCALE`, `formatDateOnly` / `formatDateTime`, Timeline dates,
  leftover `Intl.DateTimeFormat(undefined)` call sites
- `formatPluralRu(count, one, few, many)` + unit tests (1 / 21 → one;
  2–4, 22–24 → few; 0, 5–20, 11–14 → many)
- `<html lang="ru">` in `layout.tsx` **and** `global-error.tsx`
- metadata title/description Russian
- `primaryNavigation` labels
- `visualStatusLabels` + StatusBadge `aria-label`
- Shared DS defaults listed in §6
- Auth + system pages + Overview placeholder copy
- `toUserSafeMessage()` six generic branches + validation fallback
  `"Please correct the highlighted fields."`
- Update tests/E2E that assert those strings

**Excluded:** feature form/registry/object copy; enum maps other than shared
visual statuses; placeholder section titles (Phase E).

**Verify:** `npx vitest` for touched units + full `npm run test` (shared
defaults can break feature tests — fix assertions in this phase if they
target shared chrome). `npm run lint`, `typecheck`, `architecture:check`.
E2E: `auth.spec.ts` + `smoke.spec.ts` must pass; other E2E may still fail
on feature chrome until B–D — document that. Do not weaken assertions.

#### Phase B — Hazards

**Scope:** all Hazard user-facing copy, enum maps, Zod, activity titles,
toasts, empty/loading, registry columns/filters, lifecycle actions, conflict
dialogs, related-assessments chrome. Tests + `e2e/hazards.spec.ts`.

**Excluded:** RA/RC feature copy.

**Verify:** `npx vitest run src/features/hazards src/utils`;
`npm run test:e2e -- e2e/hazards.spec.ts`; lint/typecheck.

#### Phase C — Risk Assessments

Same pattern for RA. Replace `formatRiskAssessmentEnumLabel` call sites.
Profile catalog `title` fields are user-facing. `controlTypeLabel` already
exists — translate in place.

**Verify:** RA vitest + `e2e/risk-assessments.spec.ts`.

#### Phase D — Risk Controls

Same pattern for RC. Highest test cost (`risk-control-workflow.test.tsx`,
command tests, materialization, full E2E happy path). Prefer
`getByRole` / `getByLabel` with **Russian `name`**, not `getByTestId`,
unless a selector is structural and has no accessible name.

**Verify:** RC vitest + `e2e/risk-controls.spec.ts`.

#### Phase E — Placeholders, sweep, full gate

Translate placeholder pages. Grep sweep (see Verification). Full frontend
gate. Manual browser walkthrough from Acceptance Criteria.

**Excluded:** new features, Storybook copy, backend work.

---

### 8. Acceptance Criteria coverage

| AC                                                                                                                    | Phase                                                                                          |
| --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Locked EN→RU glossary referenced by implementation                                                                    | A (doc) + 3 (approval)                                                                         |
| No hardcoded English user-facing string in `app/`, `features/*`, `components/*`, `layouts/*` (stories/tests excluded) | A–E; proven in E grep                                                                          |
| `<html lang="ru">`; title/metadata Russian                                                                            | A                                                                                              |
| Nav + all routes including error/loading/not-found/forbidden/unauthorized/session-expired/login/placeholders          | A + E (placeholders)                                                                           |
| `toUserSafeMessage` + frontend-owned validation messages Russian                                                      | A (generic) + B/C/D (Zod / feature fallbacks)                                                  |
| Status/lifecycle/severity/effectiveness labels Russian and consistent                                                 | A (`visualStatusLabels`) + B/C/D (feature maps)                                                |
| Dates via explicit `"ru-RU"`                                                                                          | A                                                                                              |
| Count strings use Russian plural forms                                                                                | A (helper + shared `N selected` / table page) + B/C/D (registry `{total} total · page X of Y`) |
| lint, typecheck, test, test:e2e, architecture:check                                                                   | each phase focused; full suite in E                                                            |
| Manual spot check list                                                                                                | E                                                                                              |

---

### 9. Verification strategy

Per phase:

1. Focused Vitest for touched files.
2. Full `npm run test` after A and E (shared chrome). After B/C/D at least
   the feature file set plus any failing leftovers.
3. `npm run lint` (`--max-warnings=0`), `npm run typecheck`,
   `npm run architecture:check` each phase.
4. Playwright: A = auth+smoke; B/C/D = that feature spec; E = full
   `npm run test:e2e`.
5. Phase E residual sweep from `frontend/` (exclude `*.stories.tsx`,
   `*.test.*`, `e2e/**` fixture strings that are data):

```text
rg -n --glob '!*.stories.tsx' --glob '!*.test.*' --glob '!*.spec.ts' \
  'Sign in|Sign out|Loading|Clear all|No results|Not found|Overview|Hazards|Risk Assessments|Risk Controls|Assign owner|Submit for review|Please correct|Something went wrong|Network error' \
  src/app src/features src/components src/layouts src/lib src/services src/utils
```

Plus a second pass for leftover `Intl.DateTimeFormat(undefined` and
`formatHazardEnumLabel|formatRiskAssessmentEnumLabel|formatRiskControlEnumLabel`.

Do not add `data-testid` unless an existing test is structural and has no
stable accessible name after translation.

---

### 10. Risks

| Risk                                        | Mitigation                                                                                                                                       |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Coverage miss across ~186 TSX files         | Phase E grep + manual AC walkthrough; enum maps exhaustive vs DTO unions (`satisfies Record<Dto, string>`) so TypeScript fails on missed members |
| Terminology drift across features           | Glossary first; shared `visualStatusLabels`; Appendix A for overlapping words (Draft, Archived, Superseded, HoC)                                 |
| Test brittleness                            | Update tests in the same phase; E2E login chrome in Phase A so later phases are not blocked on Sign in                                           |
| Phase A shared defaults break feature tests | Run full Vitest after A; only change assertions that targeted shared chrome                                                                      |
| Backend 422 English leakage                 | Documented limitation; do not client-translate `error.message`                                                                                   |
| `format*EnumLabel` leftover                 | Delete or reduce to raw-token fallback; grep in E                                                                                                |
| Date assertion `Mar 1, 2027`                | Phase D E2E uses actual `Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" })` output                                                           |
| Gender/agreement debates mid-implementation | Lock Appendix A before A                                                                                                                         |

---

### 11. Known limitations

Unchanged from the TASK, plus planning evidence:

- Backend-authored validation `message` / `violations[].message` may remain
  English after mapping onto fields.
- No PDF/export/email in the frontend — nothing to translate.
- People / Knowledge / Analytics / Administration stay placeholder pages.
- Internal API throw strings (`Empty hazard response`) are not user-facing.
- Storybook remains English.
- Dev-only `error.message` on `error.tsx` / `global-error.tsx` in
  `NODE_ENV === "development"` may still show English exception text.
  Production fallback copy is Russian.

---

### 12. Implementation patterns reused

- In-place string replacement in existing label maps (Hazard/RA/RC status
  files, `visualStatusLabels`, `ACTION_LABELS`, `ACTIVITY_TITLES`).
- Explicit `Record<Dto, string>` instead of title-case helpers — same
  pattern as existing `STATUS_LABELS` / `controlTypeLabel`.
- Shared utils folder (`format-date.ts`) for locale + plural.
- Phase split like `TASK-P9-007a/b/c`.
- Plan recorded in the TASK file like `TASK-P9-006`.

---

### Appendix A — Canonical EN→RU glossary (draft, lock in Phase 3)

English left column is the **current production UI string** (or wire token
when the UI currently title-cases it). Russian is the proposed lock.

#### Navigation

| EN               | RU                     |
| ---------------- | ---------------------- |
| Overview         | Обзор                  |
| Safety           | Безопасность           |
| Hazards          | Опасности              |
| Risk Assessments | Оценки риска           |
| Risk Controls    | Меры управления риском |
| People           | Персонал               |
| Knowledge        | Знания                 |
| Analytics        | Аналитика              |
| Administration   | Администрирование      |

#### Aggregates (UI nouns)

| EN                | RU                      |
| ----------------- | ----------------------- |
| Hazard            | Опасность               |
| Risk              | Риск                    |
| Risk Assessment   | Оценка риска            |
| Risk Control      | Мера управления риском  |
| Organization      | Организация             |
| Incident          | Инцидент                |
| Inspection        | Проверка                |
| Corrective Action | Корректирующее действие |
| Training          | Обучение                |
| Permit            | Наряд-допуск            |
| Emergency Asset   | Аварийный ресурс        |
| Audit Event       | Событие аудита          |

#### Shared visual statuses (`visualStatusLabels`)

| EN                           | RU                                |
| ---------------------------- | --------------------------------- |
| Draft                        | Черновик                          |
| Under Review                 | На рассмотрении                   |
| Approved                     | Утверждено                        |
| Rejected                     | Отклонено                         |
| Planned                      | Запланировано                     |
| Active                       | Действует                         |
| In Implementation            | Внедряется                        |
| Implemented                  | Внедрено                          |
| Verified Effective           | Подтверждена эффективной          |
| Verified Partially Effective | Подтверждена частично эффективной |
| Verified Ineffective         | Подтверждена неэффективной        |
| Overdue                      | Просрочено                        |
| Suspended                    | Приостановлено                    |
| Superseded                   | Замещено                          |
| Archived                     | Архив                             |
| Cancelled                    | Отменено                          |

Hazard-only: Active → **Действует** (same chip). RA has no Active.

#### Hazard classification (replace `formatHazardEnumLabel`)

**Category:** physical Физическая; mechanical Механическая; electrical
Электрическая; chemical Химическая; biological Биологическая; ergonomic
Эргономическая; psychosocial Психосоциальная; fire_and_explosion Пожар и
взрыв; thermal Тепловая; radiation Радиационная; pressure Давление;
work_at_height Работа на высоте; confined_space Замкнутое пространство;
transport Транспортная; environmental Экологическая; dangerous_goods
Опасные грузы; process_safety Безопасность процессов; natural_hazard
Природная опасность; organizational Организационная; other Иная.

**Safety direction:** occupational_safety Охрана труда; industrial_safety
Промышленная безопасность; fire_safety Пожарная безопасность;
environmental_safety Экологическая безопасность; transport_safety
Транспортная безопасность; dangerous_goods_transport Перевозка опасных
грузов; civil_defense_and_emergency ГО и ЧС; sanitary_and_hygienic_safety
Санитарно-гигиеническая безопасность; electrical_safety Электробезопасность;
radiation_safety Радиационная безопасность.

**Source:** employee_report Сообщение работника; inspection Проверка;
incident_investigation Расследование инцидента; near_miss Микротравма /
near miss; risk_assessment Оценка риска; regulatory_assessment Регуляторная
оценка; audit Аудит; management_review Анализ со стороны руководства;
change_management Управление изменениями; equipment_documentation
Документация на оборудование; sout СОУТ; production_control
Производственный контроль; environmental_monitoring Экологический
мониторинг; transport_control Транспортный контроль; other Иной.

**Affected subject:** employee Работник; contractor Подрядчик; visitor
Посетитель; driver Водитель; passenger Пассажир; public Третьи лица;
environment Окружающая среда; equipment Оборудование; building Здание;
transport_vehicle ТС; cargo Груз; production_process Производственный
процесс.

#### Risk assessment

**Status:** same shared chips. **Risk level:** Low Низкий; Medium Средний;
High Высокий; Extreme Крайний.

**HoC:** Elimination Устранение; Substitution Замена; Engineering
Инженерные; Administrative Административные; PPE СИЗ.

**Profile titles:** Simple 3×3 Matrix Простая матрица 3×3; Simple 5×5
Matrix Простая матрица 5×5; Corporate Custom Корпоративная; Russian
Occupational Risk Профессиональный риск (РФ); Industrial Safety
Промышленная безопасность; Fire Safety Пожарная безопасность;
Environmental Risk Экологический риск; Transport Risk Транспортный риск;
ADR Risk Риск ДОПОГ (ADR).

**Object type:** workplace Рабочее место; job_position Должность;
work_activity Вид работ; equipment Оборудование; vehicle ТС;
production_process Производственный процесс; location Место;
contractor_activity Деятельность подрядчика; chemical Химическое вещество;
emergency_scenario Аварийный сценарий.

**Acceptance:** accepted Принят; conditionally_accepted Принят условно;
not_accepted Не принят; requires_escalation Требует эскалации.

**Factors:** probability Вероятность; severity Тяжесть; exposure
Экспозиция; frequency Частота; detectability Обнаружимость;
environmental_impact Экологическое воздействие; fire_consequence
Последствия пожара; business_impact Влияние на бизнес.

#### Risk control

**Status:** Draft/Planned/In Implementation/Implemented/Verified
Effective/Verified Ineffective/Suspended/Superseded/Archived/Cancelled —
same shared chips. `verified_effective` chip = Verified Effective, not a
separate “Effective”.

**Effectiveness filter:** Not verified Не подтверждена; Not applicable
Не применяется; plus the three verified results above.

**Implementation state:** Not planned Не запланировано; Planned
Запланировано; In progress — N% Выполняется — N%; Implemented Внедрено;
Not started Не начато.

**Nature:** preventive Предупреждающая; detective Выявляющая; mitigating
Снижающая; recovery Восстановительная.

**Evidence type:** document Документ; photo Фото; video Видео;
inspection_record Запись проверки; test_result Результат испытания;
work_order Наряд-заказ; training_record Запись обучения; certificate
Сертификат; measurement Измерение; approval Согласование; other Иное.

**Verification type:** initial Первичная; scheduled_review Плановый
пересмотр; post_incident После инцидента; post_inspection После проверки;
post_change После изменения; management_review Анализ руководства; other
Иная.

**Review basis:** fixed_interval Фиксированный интервал; risk_based
На основе риска; regulatory_requirement Требование НПА;
manufacturer_requirement Требование изготовителя; corporate_policy
Корпоративная политика; post_incident После инцидента; post_change После
изменения; manual Вручную.

**Owner type:** user Пользователь; employee Работник; role Роль;
organizational_unit Подразделение; external_party Внешняя сторона.

**Milestone status:** pending Ожидает; in_progress В работе; completed
Выполнено; blocked Заблокировано; cancelled Отменено.

#### Actions

| EN                                 | RU                        |
| ---------------------------------- | ------------------------- |
| Activate hazard                    | Активировать опасность    |
| Archive hazard                     | Архивировать опасность    |
| Restore hazard                     | Восстановить опасность    |
| Submit for review                  | Отправить на рассмотрение |
| Approve assessment                 | Утвердить оценку          |
| Archive assessment                 | Архивировать оценку       |
| Assign owner                       | Назначить владельца       |
| Plan implementation                | Спланировать внедрение    |
| Start implementation               | Начать внедрение          |
| Update progress                    | Обновить прогресс         |
| Add evidence                       | Добавить доказательство   |
| Complete implementation            | Завершить внедрение       |
| Verify effectiveness               | Подтвердить эффективность |
| Record verification                | Зафиксировать верификацию |
| Schedule review                    | Назначить пересмотр       |
| Complete review                    | Завершить пересмотр       |
| Suspend control                    | Приостановить меру        |
| Resume control                     | Возобновить меру          |
| Supersede control                  | Заместить меру            |
| Cancel control                     | Отменить меру             |
| Archive control                    | Архивировать меру         |
| Materialize / Materialize controls | Создать меры              |
| Save                               | Сохранить                 |
| Cancel                             | Отмена                    |
| Create                             | Создать                   |
| Edit                               | Изменить                  |
| Delete                             | Удалить                   |
| Confirm                            | Подтвердить               |
| Retry                              | Повторить                 |
| Close                              | Закрыть                   |
| Search                             | Поиск                     |
| Filters                            | Фильтры                   |
| Clear all                          | Сбросить все              |
| Previous                           | Назад                     |
| Next                               | Далее                     |
| Sign in                            | Войти                     |
| Sign out                           | Выйти                     |

#### Generic UI / errors / counts

| EN                                                        | RU                                                                                                                                                                                                                                                                 |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Loading                                                   | Загрузка                                                                                                                                                                                                                                                           |
| Loading…                                                  | Загрузка…                                                                                                                                                                                                                                                          |
| Empty state / No records found / No results               | Нет записей / Ничего не найдено (use the closer existing EN string)                                                                                                                                                                                                |
| N selected                                                | `{formatPluralRu(n, "выбрана", "выбраны", "выбрано")}` with count before the verb: `N выбрана/выбраны/выбрано` — **lock:** `Выбрано: N` to avoid gender (simpler, no plural helper on this chip). Use helper for `N мер` / `N опасностей` if a count noun appears. |
| Showing / `{total} total · page X of Y`                   | `{total} всего · страница {page} из {totalPages}`                                                                                                                                                                                                                  |
| Page X of Y                                               | Страница X из Y                                                                                                                                                                                                                                                    |
| Required field                                            | Обязательное поле                                                                                                                                                                                                                                                  |
| Network error. Check your connection and try again.       | Нет сети. Проверьте подключение и повторите попытку.                                                                                                                                                                                                               |
| Authentication required.                                  | Требуется вход.                                                                                                                                                                                                                                                    |
| You do not have permission to perform this action.        | Недостаточно прав для этого действия.                                                                                                                                                                                                                              |
| The requested resource was not found.                     | Запрашиваемый объект не найден.                                                                                                                                                                                                                                    |
| This record was updated elsewhere. Refresh and try again. | Запись изменена в другом месте. Обновите и повторите.                                                                                                                                                                                                              |
| Organization context mismatch.                            | Несовпадение контекста организации.                                                                                                                                                                                                                                |
| Please correct the highlighted fields.                    | Исправьте выделенные поля.                                                                                                                                                                                                                                         |
| Something went wrong. Try again later.                    | Что-то пошло не так. Повторите позже.                                                                                                                                                                                                                              |
| Code is required / Title is required                      | Укажите код / Укажите наименование                                                                                                                                                                                                                                 |
| Select at least one safety direction                      | Выберите хотя бы одно направление безопасности                                                                                                                                                                                                                     |

Zod messages in B/C/D follow the same tone: short imperative, no new
synonyms for Code/Title/Reason.

Activity titles follow «Опасность создана», «Оценка риска утверждена»,
«Владелец назначен», «Меры созданы из оценки риска», etc. — write the full
map in `RussianUICopy.md` during Phase A from the three `ACTIVITY_TITLES`
objects; do not improvise per screen.

System pages: Sign in → Войти; Authentication required → Требуется вход;
Access denied → Доступ запрещён; Session expired → Сеанс истек; Not found →
Страница не найдена; Unexpected error / Something went wrong → Непредвиденная
ошибка.

Placeholder body: «Заглушка маршрута для навигации. Предметный интерфейс
будет добавлен позже.»

---

### Planning report

**Documents inspected:** `AI_CONTEXT.md`, `docs/ai/DevelopmentWorkflow.md`,
`docs/tasks/TASK-P10-001-frontend-localization-ru.md`,
`docs/architecture/frontend/FrontendArchitecture.md`,
`SharedUIComponents.md`, `FrontendTesting.md`, `docs/design/README.md`,
`StatusLanguage.md`, `Forms.md`, `docs/domain/UbiquitousLanguage.md`,
`TASK-P9-006.md` (plan shape).

**Code inspected:** `layout.tsx`, `navigation.ts`, `errors.ts`,
`format-date.ts`, status/label maps, Zod schemas, validation mappers,
`ACTIVITY_TITLES`, `ACTION_LABELS`, `visualStatusLabels`, AppShell, LoginForm,
system pages, PlaceholderSectionPage, DataTable/Feedback/Filter/Dialog
defaults, E2E login selectors, representative Vitest copy assertions.

**Backend contracts:** none changed; display-only.

**Phases:** A foundations → B Hazards → C RA → D RC → E placeholders +
full gate.

**Verification:** focused Vitest per phase; full unit + E2E + grep in E.

**Risks / limitations:** see §10–11.

**Open questions:** Q1–Q6 in §3. Implementation must not start until this
plan is approved and Appendix A is locked.
