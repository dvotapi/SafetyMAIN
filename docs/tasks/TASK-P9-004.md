# TASK-P9-004 — Authentication and Application Shell

Status: **Completed**  
Date: 2026-07-25

## Goal

Integrate the frontend with production backend authentication: login/logout/refresh,
session restore, protected routes, permission-aware navigation, and authenticated shell.

## Backend addition

`GET /api/v1/auth/session` — Bearer-authenticated session bootstrap (user + active
memberships + permissions). Required because JWT does not embed RBAC permissions.

## Frontend deliverables

| Area | Implementation |
|------|----------------|
| Auth provider | `features/auth/AuthProvider.tsx` |
| Storage | sessionStorage token + org helpers |
| API | login / refresh / logout / session clients |
| API bridge | auto Bearer + `X-Organization-ID` + 401 refresh retry |
| Login page | `/login` |
| Shell gate | `AuthShellGate` |
| User menu / org display | wired in `AppShell` |
| Permission nav | `filterNavigationByPermissions` |
| Error pages | `/unauthorized`, `/forbidden`, `/session-expired` |
| Hooks | `useAuth`, `useCurrentUser`, `usePermissions`, `useOrganization`, `useAuthenticated` |
| Docs | [AuthenticationShell.md](../architecture/frontend/AuthenticationShell.md) |

## Verification

| Check | Result |
|-------|--------|
| Backend auth API tests | session endpoint covered in `test_authentication_api.py` |
| `npm run verify` | **passed** (tokens, format, lint, typecheck, architecture, unit, build) |
| `npm run build-storybook` | **passed** |
| `npm run test:e2e` | **passed** (login, logout, restore, permission nav, smoke) |
| Business Safety screens | **not implemented** |

## Deferred

Org switching, password reset, MFA/SSO, invitation UI, admin UI, httpOnly cookie transport.

## Next

**TASK-P9-005 — Hazard Management UI** (first business vertical on the authenticated shell).
