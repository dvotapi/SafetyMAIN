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

Both endpoints use the standard API error envelope and return `X-Request-ID` on
every response.

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
