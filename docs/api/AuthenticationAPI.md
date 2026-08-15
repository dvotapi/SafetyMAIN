# Authentication API

Status: Active  
Date: 2026-07-21  
Task: TASK-P3-003

Related documents:

- [AuthenticationArchitecture.md](../architecture/AuthenticationArchitecture.md)
- [IdentityDomain.md](../architecture/IdentityDomain.md)
- [APIFoundation.md](APIFoundation.md)

---

## Overview

SafetyMAIN exposes authentication endpoints under `/api/v1/auth`. Authentication is
implemented through Application handlers and Infrastructure adapters wired in
Bootstrap. Business endpoints continue to use `X-Organization-ID` and remain
unchanged in this milestone.

---

## Endpoints

| Method | Path | Operation ID | Description |
|--------|------|--------------|-------------|
| `POST` | `/api/v1/auth/login` | `auth_login` | Authenticate with email and password |
| `POST` | `/api/v1/auth/refresh` | `auth_refresh` | Exchange a refresh token for a new pair |
| `POST` | `/api/v1/auth/logout` | `auth_logout` | Revoke the presented refresh session |
| `GET` | `/api/v1/auth/session` | `auth_session` | Bootstrap the authenticated session |

Both login and refresh endpoints use the standard API error envelope and return `X-Request-ID` on
every response. The session endpoint requires a Bearer access token and does not require
`X-Organization-ID`.

---

## Login

### Request

```json
{
  "email": "operator@example.com",
  "password": "secret-password"
}
```

### Success (`200 OK`)

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Errors

| HTTP | Code | Meaning |
|------|------|---------|
| `401` | `invalid_credentials` | Unknown email or invalid password |
| `403` | `authentication_forbidden` | User exists but cannot authenticate |
| `422` | `request_validation_error` | Invalid request body |

---

## Session

### Request

Requires `Authorization: Bearer <access_token>`.

### Success (`200 OK`)

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "operator@example.com",
    "display_name": "Safety Operator",
    "status": "ACTIVE"
  },
  "memberships": [
    {
      "organization_id": "660e8400-e29b-41d4-a716-446655440001",
      "organization_name": "Acme Safety",
      "role": "admin",
      "status": "ACTIVE",
      "permissions": ["audit:read", "hazard:read", "user:read"]
    }
  ]
}
```

Only memberships with status `ACTIVE` are returned. Permissions are derived from the membership
role via `permissions_for_role`.

### Errors

| HTTP | Code | Meaning |
|------|------|---------|
| `401` | `unauthenticated` | Missing or invalid access token |

---

## Logout

### Request

```json
{
  "refresh_token": "<jwt>"
}
```

### Success (`204 No Content`)

The refresh session is revoked. Repeated calls with the same or invalid refresh token also
return `204`.

---

## Refresh

### Request

```json
{
  "refresh_token": "<jwt>"
}
```

### Success (`200 OK`)

Returns the same response shape as login.

### Errors

| HTTP | Code | Meaning |
|------|------|---------|
| `401` | `invalid_refresh_token` | Refresh token is invalid or expired |
| `422` | `request_validation_error` | Invalid request body |

---

## Bearer Authentication

OpenAPI documents a reusable scheme:

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

FastAPI dependencies are available for future protected routes:

- `get_bearer_token()` — validates `Authorization: Bearer <token>` format
- `get_authenticated_user()` — validates access token and resolves `UserId`
- `get_security_context()` — builds immutable `SecurityContext`

Business routes do **not** require Bearer authentication yet.

---

## Application Layer

| Component | Responsibility |
|-----------|----------------|
| `AuthenticateUserCommand` / `AuthenticateUserHandler` | Validate credentials and issue tokens |
| `RefreshAuthenticationCommand` / `RefreshAuthenticationHandler` | Rotate tokens from refresh token |
| `LogoutCommand` / `LogoutHandler` | Revoke refresh sessions |
| `GetAuthSessionQuery` / `GetAuthSessionHandler` | Load user profile and active memberships |

Handlers depend only on contracts:

- `UserLookupPort`
- `UserCredentialsPort`
- `PasswordHasherContract`
- `TokenServiceContract`

---

## Infrastructure

| Adapter | Contract |
|---------|----------|
| `JwtTokenService` | `TokenServiceContract` |
| `BcryptPasswordHasher` | `PasswordHasherContract` |
| `InMemoryIdentityStore` | `UserLookupPort`, `UserCredentialsPort` |

JWT signing uses symmetric HS256 by default. Token claims include `sub`, `typ`,
`iat`, and `exp`.

---

## Configuration

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_SECRET_KEY` | `dev-insecure-change-me` | Signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_TTL_SECONDS` | `3600` | Access token lifetime |
| `JWT_REFRESH_TOKEN_TTL_SECONDS` | `604800` | Refresh token lifetime |
| `JWT_ISSUER` | `safetymain` | Optional issuer claim |

Replace the default secret before production deployment.

---

## Next Step

**P3-004 — Authorization Foundation** will connect authenticated identity and
organization membership to business handlers without changing existing organization
isolation semantics.
