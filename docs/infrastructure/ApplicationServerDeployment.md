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

Browser ──HTTPS presigned PUT/GET──▶ Yandex Object Storage
                                     (storage.yandexcloud.net, SafetyMAIN bucket)
FastAPI ──HTTPS HEAD (S3 API)──────▶ same bucket
```

Frontend and API share a single public origin, so the API needs no CORS.
PostgreSQL is never part of this stack and is never exposed through the
application VDS.

Document files are the one exception to the single origin: the API only signs
presigned URLs, and the browser transfers file bytes directly to and from Yandex
Object Storage (ADR-0006). File bytes never pass through the API container.

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

Object storage (section 6): `STORAGE_ENDPOINT_URL`, `STORAGE_REGION`,
`STORAGE_BUCKET`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`,
`STORAGE_PRESIGN_TTL_SECONDS` (60–604800, default 900),
`STORAGE_MAX_UPLOAD_BYTES` (default 52428800 = 50 MB), and the read-only
`STORAGE_EXTERNAL_ACCESS_KEY` / `STORAGE_EXTERNAL_SECRET_KEY` reserved for
TASK-P11-008 (not required yet). `STORAGE_BUCKET`, `STORAGE_ACCESS_KEY`,
`STORAGE_SECRET_KEY` and an `https://` `STORAGE_ENDPOINT_URL` are mandatory in
production: the backend refuses to start without them.

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

## 6. Object storage dependency

Documents are stored in Yandex Object Storage. Provision it before deploying a
backend version that contains TASK-P11-001, otherwise startup fails validation:

1. Create a bucket for SafetyMAIN (private access, no public listing or read).
2. Create a dedicated service account with no folder-level roles (a folder
   role such as `storage.editor` would reach every bucket in the folder,
   including `hr_form` buckets). Grant it `READ` and `WRITE` on this bucket
   only, through the bucket ACL:

   ```bash
   yc storage bucket update --name <bucket> \
     --grants grant-type=grant-type-account,grantee-id=<sa-id>,permission=permission-read \
     --grants grant-type=grant-type-account,grantee-id=<sa-id>,permission=permission-write
   ```

   Create a static access key for it (`yc iam access-key create
   --service-account-name <sa-name>`) and put the key id and secret into
   `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY`; never reuse the `hr_form`
   credential.
3. Set `STORAGE_ENDPOINT_URL=https://storage.yandexcloud.net`,
   `STORAGE_REGION=ru-central1` and `STORAGE_BUCKET=<bucket>`.
4. Apply a CORS rule that admits the public SafetyMAIN origin only:

   ```bash
   cat > cors.json <<'JSON'
   {
     "CORSRules": [
       {
         "AllowedOrigins": ["https://<safetymain-domain>"],
         "AllowedMethods": ["PUT", "GET", "HEAD"],
         "AllowedHeaders": ["content-type", "x-amz-meta-sha256"],
         "ExposeHeaders": ["ETag"],
         "MaxAgeSeconds": 3600
       }
     ]
   }
   JSON
   aws s3api put-bucket-cors --endpoint-url https://storage.yandexcloud.net \
     --bucket <bucket> --cors-configuration file://cors.json
   ```

Presigned URLs are signed for the host in `STORAGE_ENDPOINT_URL`, so that
endpoint must be reachable both from the application VDS (the API checks
uploaded objects with `HEAD`) and from users' browsers. Do not point it at an
internal-only address.

A presigned upload pins `Content-Type`, `Content-Length` and the
`x-amz-meta-sha256` header; storage rejects a transfer that differs in any of
them. The SHA-256 is computed by the client and is not re-verified server-side
yet.

## 7. Migration procedure

Migrations always run before the backend starts, from the same image:

```bash
cd /srv/safetymain/app/infrastructure/production
docker compose --profile migrate run --rm --entrypoint alembic migrate current
docker compose --profile migrate run --rm migrate          # alembic upgrade head
```

If a migration fails, do not start the backend: report the failing revision,
the current database revision and the expected head. Never downgrade or reset
the production database as part of a deployment.

## 8. Startup, shutdown, update, rollback

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

## 9. Identity bootstrap

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

## 10. Health checks

| Check | Command |
|-------|---------|
| Backend process | `curl -s https://<domain>/api/v1/health` |
| Backend + database | `curl -s https://<domain>/api/v1/ready` |
| Frontend | `curl -sI https://<domain>/login` |
| Container health | `docker ps --filter name=safetymain` |

`/api/v1/ready` performs `SELECT 1` against PostgreSQL; a healthy container
alone is not evidence of a successful deployment.

## 11. Logs

```bash
docker logs -f safetymain-backend      # startup, request and error logs
docker logs -f safetymain-frontend     # Next.js server
docker logs -f caddy-proxy             # reverse proxy and ACME
```

Both application containers use the `json-file` driver capped at 10 MB × 5
files, so log growth is bounded. Startup logging reports only `app_env`,
`jwt_algorithm`, whether an issuer is configured, and `auth_enforcement` —
never the JWT secret, the database URL, or any token.

## 12. Reverse proxy integration

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

## 13. Known limitations

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
- Object storage is provisioned by hand (bucket, service account, CORS); there
  is no infrastructure-as-code for it yet. Objects are never deleted by the
  application (ADR-0006).
