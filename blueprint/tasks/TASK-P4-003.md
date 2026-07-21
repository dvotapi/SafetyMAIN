# TASK-P4-003

## Title

Production Security Configuration

## Status

Completed (2026-07-21)

## Summary

Added centralized startup validation for security-related settings so production
deployments fail fast on unsafe or inconsistent JWT, issuer, enforcement, and
database configuration.

## Validation Rules

- JWT algorithm must be one of `HS256`, `HS384`, `HS512`
- Access and refresh TTLs must be positive, within documented ranges, and refresh must exceed access
- JWT issuer may be omitted in non-production environments; whitespace-only values are rejected
- `AUTH_ENFORCEMENT` must resolve to a boolean during settings parsing
- Production additionally requires:
  - non-placeholder JWT secret with minimum 32 characters
  - configured issuer
  - `AUTH_ENFORCEMENT=true`
  - `DATABASE_URL` for persistent identity

## Startup Behavior

- `load_settings()` validates after parsing environment variables
- `create_container()` validates before constructing adapters
- `create_app()` validates before attaching the container and logs non-sensitive security metadata once

## Configuration Examples

Development:

```env
APP_ENV=development
JWT_SECRET_KEY=dev-insecure-change-me
AUTH_ENFORCEMENT=false
```

Production:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=<32+ character random secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_TTL_SECONDS=3600
JWT_REFRESH_TOKEN_TTL_SECONDS=604800
JWT_ISSUER=safetymain-prod
AUTH_ENFORCEMENT=true
```

Generate production secrets with a cryptographically secure generator, for example:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Tests Added

- `tests/bootstrap/test_security_validation.py`

## Deployment Guidance

See [ProductionSecurityConfiguration.md](../docs/architecture/ProductionSecurityConfiguration.md).

## Verification Results

- Full pytest suite
- Ruff clean

## Follow-Up Work

- Integrate external secret management when deployment platform is selected
- Consider staging-specific hardening policy if required by operations
