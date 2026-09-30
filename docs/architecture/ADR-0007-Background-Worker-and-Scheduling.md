# ADR-0007 — Background Worker and Scheduling

**Status:** Accepted

**Date:** 2026-09-14

**Authors:** SafetyMAIN Architecture Team

---

# Context

ADR-0004 lists "Scheduled evaluation" and "Date expiration" as Compliance Rule triggers.

ADR-0005 requires continuous evaluation of approaching deadlines and overdue obligations.

Both decisions are conceptual. Nothing in the platform runs outside an HTTP request today.

Epic P11 needs work that no user request should wait for:

- evaluating obligations and deadlines;
- dispatching notifications;
- synchronising employees from `hr_form`;
- processing uploaded documents with AI;
- watching regulatory sources.

Current state:

- the backend runs as one API process created by `create_app()`;
- dependency wiring lives in the composition root `AppContainer` (`backend/bootstrap/container.py`), persistence uses the Unit-of-Work;
- `backend/core/infrastructure/messaging/` is an empty package; `pyproject.toml` has no scheduler or queue dependency;
- the production stack (`infrastructure/production/compose.yml`) runs `backend`, `frontend`, and a one-shot `migrate` service; PostgreSQL runs on a separate server;
- no Redis exists in any stack.

The Architecture Decision Freeze (§6 Hybrid Storage Model) lists Redis.

---

# Decision

SafetyMAIN introduces a second process, `safetymain-worker`.

- It is built from the same backend image as the API.
- It is started with a different command.
- It shares settings, container wiring (`AppContainer`), and the Unit-of-Work with the API.

Jobs call the same application handlers the API uses. Business logic is not implemented a second time for background execution.

A job that acts on organization-owned data carries its organization and runs under the same tenant isolation, authorization, and audit rules as an API request.

---

# Job Persistence

Jobs are persisted in the PostgreSQL table `scheduled_jobs`:

| Column | Meaning |
|---|---|
| `id` | Job identifier |
| `kind` | Registered job kind |
| `payload` | Job parameters |
| `run_at` | Earliest time the job may run |
| `locked_at` | Time a worker took the job |
| `locked_by` | Worker that took the job |
| `attempts` | Number of attempts so far |
| `last_error` | Error of the last failed attempt |
| `status` | Job status |

This column list is the minimum. The implementing task may add columns; it may not remove these.

Workers take jobs with `SELECT … FOR UPDATE SKIP LOCKED`, so several workers never take the same job.

No Redis and no Celery are introduced for now.

---

# Recurring Schedules

- Recurring schedules are declared in code as a registry of `kind → cron`.
- A scheduler loop materialises due schedules into `scheduled_jobs` rows.
- A run is idempotent and safe to repeat: a retry, a duplicate materialisation, or a restart after a crash produces the same result.

Schedules are platform mechanics (Freeze §13 Code Describes the Platform).

What a job evaluates — deadlines, warning thresholds per `DocumentType`, applicability — stays in metadata and Compliance Rules (ADR-0003, ADR-0004; Freeze §14, §15). Changing a business threshold never requires a code change.

---

# Job Kinds Foreseen by P11

| Kind | Schedule | Purpose | Introduced by |
|---|---|---|---|
| `evaluate_obligations` | daily | Obligation and deadline evaluation (ADR-0005) | P11-006 |
| `dispatch_notifications` | every N minutes | Delivery of pending notifications | P11-007 |
| `sync_hr` | hourly | Employee read-model sync from `hr_form` (ADR-0008) | P11-004 |
| `process_document_ai` | on demand | AI processing of uploaded documents (ADR-0009) | P11-002 |
| `watch_regulations` | daily | Regulatory source monitoring | P11-010 |

`N` is a setting of the implementing task.

---

# Run Records and Failure Isolation

- Every job run is recorded for operators: start, end, outcome, error.
- The storage shape of run records (additional columns or a separate run history table) is decided by the implementing task.
- Job failures never break API requests. The API never waits for a job to finish, and a failed job does not roll back the request that created it.
- Run records and `last_error` follow the same sensitive-data rule as audit metadata: no credentials, tokens, or document contents.

---

# Deployment

- The production compose stack gains a `worker` service running the backend image with the worker command.
- The worker health check is: last successful scheduler tick less than 5 minutes ago.
- The worker serves no HTTP traffic and needs no host port or reverse-proxy alias.
- The API health endpoint is unchanged.

---

# Migration Path to a Message Broker

PostgreSQL remains the job queue until measured throughput or latency requires more, for example sustained lock contention on `scheduled_jobs` or polling delay beyond what a job kind tolerates.

The path:

1. Job handlers are resolved through the kind registry and do not depend on how a job is delivered.
2. Access to `scheduled_jobs` stays inside `backend/core/infrastructure/`.
3. A broker-backed delivery replaces PostgreSQL polling without changing job handlers.

Selecting a broker requires a new ADR.

---

# Impact on Architecture Decision Freeze

The Architecture Decision Freeze §6 lists Redis.

This ADR does not introduce Redis for the P11 scope and does not remove Redis from the Hybrid Storage Model. A future need for Redis (caching or message brokering) is decided by its own ADR.

---

# Principles

- One image, two processes.
- PostgreSQL is the job queue until proven insufficient.
- Every job is idempotent.
- Schedules live in code; business thresholds live in metadata.
- Background failures stay in the background.
- Jobs obey the same tenant isolation, authorization, and audit rules as requests.

---

# Consequences

- The first P11 task that needs a background job introduces the worker entry point, the `scheduled_jobs` migration, the scheduler loop, run records, and the production `worker` service. By the epic sequence this is P11-002 (`process_document_ai`) or P11-004 (`sync_hr`), whichever is implemented first.
- That task updates `infrastructure/production/compose.yml` and `docs/infrastructure/ApplicationServerDeployment.md`.
- Two processes share the database; connection capacity is planned for both.
- The ADR-0004 triggers "Scheduled evaluation" and "Date expiration" and the ADR-0005 monitoring gain an execution vehicle. Reminders remain implementations of the Obligations Engine (ADR-0005), not independent jobs.
- Exposing job runs through the API or UI is not decided here.

---

# Related ADRs

- ADR-0003 Metadata Engine
- ADR-0004 Compliance Rules Engine
- ADR-0005 Obligations Engine
- ADR-0006 Document and Evidence Storage
- ADR-0008 HR Integration Contract
- ADR-0009 Knowledge Blocks and Document Assembly

---

# Decision Summary

Background work runs in `safetymain-worker`, a second process built from the backend image.

Jobs are stored in PostgreSQL and taken with `SELECT … FOR UPDATE SKIP LOCKED`.

Recurring schedules are declared in code; business thresholds stay in metadata.

No Redis or Celery is introduced for P11; a broker requires a future ADR.
