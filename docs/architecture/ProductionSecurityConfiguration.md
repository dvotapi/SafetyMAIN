# Production Security Configuration

Status: Active  
Date: 2026-07-21  
Task: TASK-P4-003

Related documents:

- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)
- [SecurityEnforcementRollout.md](SecurityEnforcementRollout.md)
- [IdentityPersistence.md](IdentityPersistence.md)

---

## 1. Supported Configuration

Security-related settings are loaded from the environment by
`backend/bootstrap/settings.py` and validated by
`backend/bootstrap/security_validation.py`.

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Symmetric signing secret for access and refresh tokens |
| `JWT_ALGORITHM` | Supported JWT signing algorithm |
| `JWT_ACCESS_TOKEN_TTL_SECONDS` | Access token lifetime |
| `JWT_REFRESH_TOKEN_TTL_SECONDS` | Refresh token lifetime |
| `JWT_ISSUER` | Optional issuer claim validated on decode |
| `AUTH_ENFORCEMENT` | Enables authenticated tenant and RBAC enforcement |
| `DATABASE_URL` | Required in production for persistent identity |
| `APP_ENV` | Deployment profile selector (`development`, `test`, `production`) |

Authentication, authorization, tenant isolation, RBAC, and business API behavior
are unchanged by this task. Validation only prevents unsafe startup
configuration.

---

## 2. Startup Validation

Validation runs:

1. after `load_settings()` parses environment variables;
2. at the start of `create_container()` before adapter construction;
3. in `create_app()` before the application serves requests.

Startup fails fast with `SecurityConfigurationError` when configuration is
invalid. Sensitive values are not included in error messages.

Non-sensitive startup logging is emitted once by
`backend/bootstrap/startup_logging.py`:

- `app_env`
- `jwt_algorithm`
- whether an issuer is configured (boolean only)
- `auth_enforcement`

Secrets, password hashes, and tokens are never logged.

---

## 3. Required Production Settings

When `APP_ENV=production`, SafetyMAIN requires:

| Setting | Requirement |
|---------|-------------|
| `JWT_SECRET_KEY` | Non-empty, at least 32 characters, not a known development placeholder |
| `JWT_ALGORITHM` | One of `HS256`, `HS384`, `HS512` |
| `JWT_ACCESS_TOKEN_TTL_SECONDS` | 60–86400 |
| `JWT_REFRESH_TOKEN_TTL_SECONDS` | 300–7776000 and greater than access TTL |
| `JWT_ISSUER` | Configured non-empty issuer |
| `AUTH_ENFORCEMENT` | `true` |
| `DATABASE_URL` | Configured persistent database URL |

Rejected placeholder secrets include values such as `secret`, `changeme`,
`development`, `dev-secret`, `test-secret`, and the development default
`dev-insecure-change-me`.

---

## 4. Compatibility Mode

`AUTH_ENFORCEMENT=false` remains supported in development and during client
migration.

Compatibility mode is not automatically enabled or disabled by validation.
Production deployments must set `AUTH_ENFORCEMENT=true` explicitly.

---

## 5. Enforcement Mode

When `AUTH_ENFORCEMENT=true`:

- business routes require Bearer access tokens;
- membership and RBAC checks run through existing dependencies;
- refresh tokens cannot authorize business requests.

Production validation requires enforcement mode to be enabled.

---

## 6. JWT Recommendations

### Secret generation

Use a cryptographically secure random secret with at least 32 characters:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Store the secret in the deployment environment or secret manager. Never commit
production secrets to source control.

### Algorithm

Use `HS256` unless operational policy requires `HS384` or `HS512`. Unsupported
algorithms are rejected at startup.

### Issuer

Configure a stable issuer value per deployment environment, for example
`safetymain-prod`. Issuer validation at decode time remains unchanged from P3.

An empty issuer (`JWT_ISSUER=` or unset in non-production) disables issuer claim
enforcement.

---

## 7. Environment Profiles

### Development

- optional database;
- development JWT secret permitted;
- manual identity seed available;
- `AUTH_ENFORCEMENT=false` supported.

### Testing

- deterministic isolated secrets in test fixtures;
- `APP_ENV=test` skips production-only hardening while still validating TTL and algorithm rules;
- reproducible authentication behavior.

### Production

- persistent identity through PostgreSQL;
- strong non-placeholder JWT secret;
- configured issuer;
- `AUTH_ENFORCEMENT=true`;
- no development defaults.

No profile framework is implemented. Profiles are documented deployment
expectations only.

---

## 8. Deployment Checklist

1. Set `APP_ENV=production`.
2. Configure `DATABASE_URL` and run Alembic migrations.
3. Generate and configure a strong `JWT_SECRET_KEY`.
4. Set `JWT_ISSUER` to the deployment issuer value.
5. Set `AUTH_ENFORCEMENT=true`.
6. Confirm token lifetimes meet operational policy.
7. Seed identity data manually in non-production environments only.
8. Verify startup succeeds and `/api/v1/ready` reports database readiness.

---

## 9. Operational Guidance

- Rotate JWT secrets through a controlled re-deployment; existing tokens become invalid after secret rotation.
- Keep development defaults out of production environment files.
- Treat `403 permission_denied` and `401 unauthenticated` as expected client/integration outcomes after enforcement rollout.
- Monitor startup logs for validation success without expecting secret values to appear in logs.

---

## 10. Known Limitations

1. Validation is environment-aware for production hardening only; staging is not separately classified.
2. Secret management services (Vault, cloud secret stores) are not integrated in this task.
3. OpenAPI still documents the enforced-mode Bearer contract regardless of runtime enforcement mode.
