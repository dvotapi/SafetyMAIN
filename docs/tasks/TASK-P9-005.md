# TASK-P9-005 — Hazard Management UI

Status: **Completed**  
Date: 2026-07-25

## Implementation summary

Delivered the first SafetyMAIN frontend business vertical: Hazard Registry, Create, and Object Page, integrated with the production Hazard API, authenticated shell, shared UI, TanStack Query, and permission-aware navigation under Safety → Hazards.

## Frontend routes

| Route | Page |
|-------|------|
| `/safety/hazards` | Registry |
| `/safety/hazards/new` | Create |
| `/safety/hazards/[hazardId]` | Object page |

## Backend endpoints used

`GET/POST /api/v1/hazards`, `GET/PATCH /api/v1/hazards/{id}`, activate/archive/restore, related `GET /api/v1/risk-assessments?hazard_id=`, activity via `GET /api/v1/admin/audit-events`.

## Permissions used

`hazard:read|create|update|activate|archive|restore`, `risk:read`, `audit:read`.

## Feature structure

`frontend/src/features/hazards/` with public exports limited to the three pages via `index.ts`.

## Shared components reused

Registry*, DataTable, ObjectHeader/ObjectTabs, StatusBadge, Form/RHF adapters, FilterBar/FilterChip/Search, Dialogs/SideDrawer, EmptyState/LoadingState/Alert/Toast, Timeline, NextActionCard, Panel/PropertyGrid/DescriptionList, PageContainer/PageHeader.

## New shared components

None required for this slice.

## Registry capabilities

Search, status/category/source filters, include archived, URL state, server pagination, empty/filtered-empty/error+retry, permission-gated create.

## Form capabilities

Zod + RHF create/edit, backend validation/conflict mapping, duplicate-submit prevention, source immutable after activation.

## Lifecycle actions

Activate (draft), archive (draft/active + reason), restore (archived + reason).

## Optimistic concurrency

`expected_version` on mutations; `409` → conflict dialog with reload.

## Related Risk Assessments

Read-only table + risk summary from backend fields only.

## Activity data source

Admin audit events (`resource_type=HAZARD`) when `audit:read`; otherwise documented unavailable state.

## Backend changes

None beyond existing session/hazard contracts. Frontend `normalizeApiError` unwraps `{ error: { code, message } }` envelopes.

## Verification results

| Check | Result |
|-------|--------|
| Unit/component tests | **27 passed** |
| E2E | **9 passed** (auth + hazards + smoke) |
| Storybook | `npm run build-storybook` passed |
| `npm run verify` | **passed** |
| Architecture check | passed (hazard API isolation rule added) |
| Backend hazard tests | unchanged contract; suite remains green |

## Known limitations / deferred

Risk Assessment UI, Risk Control UI, attachments, bulk ops, export, org switching, user-configurable sort.

## Recommended next task

**TASK-P9-006 — Risk Assessment Management UI**
