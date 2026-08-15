# Hazard Management UI

Status: Active  
Date: 2026-07-25  
Task: [TASK-P9-005](../../tasks/TASK-P9-005.md)

Related:

- [HazardsAPI.md](../../api/HazardsAPI.md)
- [AuthenticationShell.md](AuthenticationShell.md)
- [SharedUIComponents.md](SharedUIComponents.md)

## Feature structure

```text
frontend/src/features/hazards/
  api/           # transport + TanStack Query
  components/    # Hazard-specific presentation
  pages/         # Registry / Create / Object
  schemas/       # Zod form models
  mappers/       # DTO ↔ view/form
  hooks/         # permission capabilities
  utils/         # status + URL state
  index.ts       # public page exports only
```

Routes (thin app wrappers):

- `/safety/hazards`
- `/safety/hazards/new`
- `/safety/hazards/[hazardId]`

## Backend endpoints used

| Operation | Method / path |
|-----------|----------------|
| List | `GET /api/v1/hazards` |
| Read | `GET /api/v1/hazards/{id}` |
| Create | `POST /api/v1/hazards` |
| Update | `PATCH /api/v1/hazards/{id}` |
| Activate | `POST .../activate` |
| Archive | `POST .../archive` |
| Restore | `POST .../restore` |
| Related RA | `GET /api/v1/risk-assessments?hazard_id=` |
| Activity | `GET /api/v1/admin/audit-events?resource_type=HAZARD&resource_id=` |

No server-side sort parameters — ordering is backend-fixed (`created_at DESC`).

## Permissions

`hazard:read|create|update|activate|archive|restore`, plus `risk:read` (related assessments) and `audit:read` (activity).

Capabilities are mapped in `mapHazardCapabilities` / `useHazardPermissions` — never by role name.

## Query keys and cache

Keys are scoped by `organizationId` via `hazardKeys.*`. Logout clears the QueryClient through AuthProvider. Mutations invalidate list + detail for the active organization only.

## Forms and concurrency

Create/edit use React Hook Form + Zod. Mutations send `expected_version`. `409 hazard_version_conflict` opens `HazardConflictDialog` (reload latest; no auto-retry).

## Related assessments and activity

Related Risk Assessments are read-only. RA object pages are deferred. Activity uses real audit events when `audit:read` is present; otherwise an empty/unavailable state is shown — no fake client history.

## Organization isolation

All requests use the API auth bridge (`Bearer` + `X-Organization-ID`). Cross-tenant missing resources surface as not-found.

## Known limitations

- No CSV export, attachments, comments, bulk edit, or org switching
- Registry sorting is not user-configurable (backend contract)
- Activity requires admin audit permission
- Risk Assessment UI deferred to P9-006

## Testing

Unit: mappers, status, permissions, query keys, URL state, schema.  
E2E (mocked API): create → edit → activate → registry; read-only create blocked; unknown → not found; conflict dialog.
