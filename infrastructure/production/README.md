# SafetyMAIN production stack

Docker Compose definition for the application server: the FastAPI backend, the
Next.js frontend, and a one-shot Alembic migration runner. PostgreSQL is **not**
part of this stack — it runs on a dedicated database server.

Full runbook: [`docs/infrastructure/ApplicationServerDeployment.md`](../../docs/infrastructure/ApplicationServerDeployment.md).

## Files

| File | Purpose |
|------|---------|
| `compose.yml` | Production stack (`backend`, `frontend`, `migrate` profile) |
| `backend.Dockerfile` | Backend image; build context is the repository root |
| `frontend.Dockerfile` | Frontend image; build context is `frontend/` |
| `.env.example` | Template for the runtime configuration — placeholders only |

## First deployment

```bash
cp .env.example .env && chmod 600 .env    # fill in real values, never commit
docker network create safetymain-edge     # shared with the reverse proxy
docker compose --profile migrate run --rm migrate
docker compose up -d
```

## Daily operations

```bash
docker compose ps
docker compose logs -f backend
docker compose up -d          # apply a rebuilt image
docker compose down           # stop the stack
```

## Rules

- `.env` holds the database password and the JWT signing secret. It stays out
  of Git; on the server it is a symlink to a root-only file.
- Host ports are bound to `127.0.0.1` only. Public traffic arrives exclusively
  through the reverse proxy on the host.
- Never add a PostgreSQL service here.
- Everything under `NEXT_PUBLIC_*` is visible to browser users and is baked into
  the frontend image at build time.
