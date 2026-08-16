# Application Server Deployment

Manual, reproducible deployment of SafetyMAIN onto the shared application VDS.
This is the known-good procedure a later CI/CD pipeline must be able to execute
without redesign.

## 1. Architecture

```
Internet
   │ HTTPS (Let's Encrypt, Caddy-managed)
   ▼
Caddy (existing shared reverse proxy, container `caddy-proxy`)
   │
   ├── /       → safetymain-web:3100     (Next.js production server)
   └── /api/*  → safetymain-api:8000     (FastAPI / uvicorn)
                        │
                        │ PostgreSQL over TLS (sslmode=require)
                        ▼
                Dedicated database server
                   database `safetymain`, role `safetymain_app`
```

Frontend and API share a single public origin, so the browser never talks to a
second host and CORS stays disabled. PostgreSQL is never part of this stack and
is never exposed through the application VDS.

## 2. Server layout

| Path | Contents |
|------|----------|
| `/srv/safetymain/app` | Git clone of the deployed commit |
| `/srv/safetymain/app/infrastructure/production` | Compose stack, Dockerfiles |
| `/srv/safetymain/app/infrastructure/production/.env` | Symlink to the secret file |
| `/srv/safetymain/secrets/production.env` | Runtime secrets, root-only (`600`) |
| `/srv/safetymain/secrets/db-credentials.env` | Copy of the database credential, root-only |
| `/root/caddy/Caddyfile` | Shared reverse-proxy configuration |

Secrets live outside the Git working tree; `.env` inside the repository
directory is only a symlink and is excluded from every deployment sync.

## 3. Docker services

| Service | Container | Internal port | Host binding | Restart policy |
|---------|-----------|---------------|--------------|----------------|
| `backend` | `safetymain-backend` | 8000 | `127.0.0.1:8100` | `unless-stopped` |
| `frontend` | `safetymain-frontend` | 3100 | `127.0.0.1:3100` | `unless-stopped` |
| `migrate` | ephemeral (`--profile migrate`) | — | — | `no` |

Networks:

- `safetymain_default` — internal traffic and outbound database connections.
- `safetymain-edge` — external network shared with `caddy-proxy`; the proxy
  addresses the containers by the aliases `safetymain-api` and `safetymain-web`.

Both containers run with `no-new-privileges`, without privileged mode and
without access to the Docker socket.

## 4. Environment variables

Backend runtime (`/srv/safetymain/secrets/production.env`, template:
`infrastructure/production/.env.example`):

`APP_NAME`, `APP_VERSION`, `APP_ENV=production`, `DATABASE_URL`,
`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ISSUER`,
`JWT_ACCESS_TOKEN_TTL_SECONDS`, `JWT_REFRESH_TOKEN_TTL_SECONDS`,
`JWT_REFRESH_ABSOLUTE_TTL_SECONDS`, `REFRESH_TOKEN_ROTATION_ENABLED`,
`AUTH_ENFORCEMENT=true`, `CORS_ALLOWED_ORIGINS`.

Frontend build-time (same file; consumed as Compose build arguments):
`NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV`.

`NEXT_PUBLIC_*` values are inlined into the client bundle by `next build`.
Changing them requires rebuilding the frontend image, and they must never carry
a secret.

Deployment knobs: `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT`,
`SAFETYMAIN_IMAGE_TAG`.

Validation rules for the security-relevant values are enforced at startup by
`backend/bootstrap/security_validation.py`; see
`docs/architecture/ProductionSecurityConfiguration.md`.

## 5. Database dependency

The database is provisioned on the database server before deployment:
database `safetymain`, login role `safetymain_app`, and a `pg_hba.conf` rule
that permits `hostssl` connections only from the application VDS address and
rejects that role from anywhere else. The application VDS never administers the
database server.

## 6. Migration procedure

Migrations always run before the backend starts, from the same image:

```bash
cd /srv/safetymain/app/infrastructure/production
docker compose --profile migrate run --rm --entrypoint alembic migrate current
docker compose --profile migrate run --rm migrate          # alembic upgrade head
```

If a migration fails, do not start the backend: report the failing revision,
the current database revision and the expected head. Never downgrade or reset
the production database as part of a deployment.

## 7. Startup, shutdown, update, rollback

```bash
cd /srv/safetymain/app/infrastructure/production

# Start (or restart) the stack
docker compose up -d

# Stop the stack; unrelated services and the reverse proxy are untouched
docker compose down

# Update to a new commit
git -C /srv/safetymain/app fetch origin
git -C /srv/safetymain/app checkout <commit-sha>
docker compose build
docker compose --profile migrate run --rm migrate
docker compose up -d

# Rollback: check out the previous commit and rebuild
git -C /srv/safetymain/app checkout <previous-commit-sha>
docker compose build && docker compose up -d
```

Rollback covers application code only. A migration that has already been
applied is rolled back deliberately and separately, never automatically.

## 8. Identity bootstrap

An empty production database has no user, and users can only be created by an
already authenticated admin. `scripts/bootstrap_admin.py` breaks that cycle
exactly once: it creates the first organization, the first user and an ACTIVE
`admin` membership, and refuses to run when any user already exists.

```bash
docker compose --profile migrate run --rm \
  -v /srv/safetymain/secrets/bootstrap-admin-password.txt:/run/secrets/bootstrap-admin-password:ro \
  --entrypoint python migrate -m scripts.bootstrap_admin \
  --email <admin-email> --display-name "<name>" --organization "<org>" \
  --password-file /run/secrets/bootstrap-admin-password
```

The initial password is generated on the server and stored root-only. The API
currently exposes no password-change or password-reset operation, so rotating
it means re-hashing the credential directly against the database until such an
endpoint exists. Every later account goes through `POST /api/v1/admin/users`.

## 9. Health checks

| Check | Command |
|-------|---------|
| Backend process | `curl -s https://<domain>/api/v1/health` |
| Backend + database | `curl -s https://<domain>/api/v1/ready` |
| Frontend | `curl -sI https://<domain>/login` |
| Container health | `docker ps --filter name=safetymain` |

`/api/v1/ready` performs `SELECT 1` against PostgreSQL; a healthy container
alone is not evidence of a successful deployment.

## 10. Logs

```bash
docker logs -f safetymain-backend      # startup, request and error logs
docker logs -f safetymain-frontend     # Next.js server
docker logs -f caddy-proxy             # reverse proxy and ACME
```

Both application containers use the `json-file` driver capped at 10 MB × 5
files, so log growth is bounded. Startup logging reports only `app_env`,
`jwt_algorithm`, whether an issuer is configured, and `auth_enforcement` —
never the JWT secret, the database URL, or any token.

## 11. Reverse proxy integration

The SafetyMAIN virtual host is appended to the shared `/root/caddy/Caddyfile`
following the conventions already used by the other applications on the server.
Validate before applying, and prefer a reload over a restart:

```bash
docker exec caddy-proxy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker exec caddy-proxy caddy reload   --config /etc/caddy/Caddyfile --adapter caddyfile
```

The Caddyfile is bind-mounted into the container by inode. Editing it with a
tool that replaces the file (`mv`, or an editor that writes through a rename)
leaves the container reading the old content, and the reload then reports
`config is unchanged`. Write in place (`cp` over the existing file), or
recreate the container with `docker compose up -d` in `/root/caddy` — which
briefly interrupts every site on the server and therefore needs owner approval.

## 12. Known limitations

- The frontend image runs `next start` with the full production dependency
  tree. Next.js `output: "standalone"` would shrink it, but that is an
  application configuration change and was left out of this deployment.
- No CI/CD: builds and migrations are run manually on the server, by design.
  The Compose definition is written so a pipeline can execute the same steps.
- Images are tagged `latest` only; there is no image registry yet, so rollback
  is by Git commit plus rebuild rather than by pulling a previous image.
- `scripts/bootstrap_admin.py` records no administrative audit event, because
  no acting principal exists before the first user.
- There is no password-change or password-reset endpoint yet, so the initial
  admin password cannot be rotated through the application.
