# Frontend Authentication Shell

Status: Active  
Date: 2026-07-25  
Task: [TASK-P9-004](../../tasks/TASK-P9-004.md)

Related:

- [AuthenticationAPI.md](../../api/AuthenticationAPI.md)
- [RefreshTokenSessions.md](../RefreshTokenSessions.md)
- [SharedUIComponents.md](SharedUIComponents.md)

## Lifecycle

```text
restoring → unauthenticated | authenticated
unauthenticated → authenticating → authenticated
authenticated → refreshing → authenticated | expired
logout → unauthenticated
```

## Providers and hooks

| API | Role |
|-----|------|
| `AuthProvider` | Session restore, login/logout/refresh, org selection (display) |
| `useAuth()` | Full auth state + actions |
| `useCurrentUser()` | User profile |
| `usePermissions()` / `hasPermission` | Permission checks |
| `useOrganization()` | Active organization display |
| `useAuthenticated()` | Boolean gate |

## Token persistence

Access + refresh tokens live in **sessionStorage** (tab-scoped). Documented as bootstrap persistence; httpOnly cookie strategy is a future hardening item.

## API integration

`services/api/auth-bridge` binds token and `X-Organization-ID` providers into `ApiClient`. On `401` (non-auth routes), the client attempts a single refresh, then retries once.

## Session bootstrap

`GET /api/v1/auth/session` returns user + active memberships with permission strings. Frontend picks the first membership (or last-selected org id) as current organization. **Organization switching UI is deferred.**

## Route protection

`AuthShellGate` wraps the app:

- Public: `/login`, `/unauthorized`, `/forbidden`, `/session-expired`
- All other routes require `authenticated` (or in-flight `refreshing`)
- Anonymous access redirects to `/login?next=…`
- Expired refresh redirects to `/session-expired`

## Permission-aware navigation

`filterNavigationByPermissions` hides sections/items whose `requiredPermission` is missing (e.g. Administration needs `user:read`).

## Known limitations

- No password reset / MFA / SSO
- No org switcher dropdown (display only)
- No invitation acceptance UI
- sessionStorage is not cross-tab; closing the tab ends the SPA session store (refresh token may still be valid server-side until logout/expiry)
