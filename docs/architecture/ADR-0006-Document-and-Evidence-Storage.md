# ADR-0006 — Document and Evidence Storage

**Status:** Proposed

**Date:** 2026-09-14

**Authors:** SafetyMAIN Architecture Team

---

# Context

Documents are generated evidence, not the source of truth (ADR-0001, ADR-0005).

Evidence still has to be kept as files: approved local normative acts, signed orders, scanned originals, generated instructions, printable journal forms, and employee permit documents.

Epic P11 needs file storage for:

- existing PDF instructions uploaded for decomposition (P11-001, P11-002);
- generated compliance documents (P11-003);
- printable journal forms (P11-005);
- employee permit documents that `hr_form` already stores (P11-008).

The platform has no file store today:

- `backend/core/infrastructure/storage/` is an empty package;
- `pyproject.toml` has no object storage client dependency;
- `backend/core/contracts/storage.py` declares an unused placeholder `StorageContract` that streams bytes through the calling process (`put`, `open`) and exposes `delete`.

The Architecture Decision Freeze (§6 Hybrid Storage Model) lists MinIO as part of the primary storage architecture.

`hr_form` already stores employee files in Yandex Object Storage.

Numbering note: ADR numbers marked "(planned)" in the Related ADRs sections of ADR-0001…ADR-0005 (for example "ADR-0006 Event Engine" or "ADR-0007 Knowledge Graph") were placeholders, not reservations. ADR-0006…ADR-0010 are assigned to the P11 decisions. The Event Engine and Knowledge Graph ADRs receive the next free numbers when they are written.

---

# Decision

S3-compatible object storage is the only file store of SafetyMAIN.

- Development: a MinIO service in the repository `docker-compose.yml`.
- Production: Yandex Object Storage, the same provider `hr_form` already uses.

Files are not stored on application container disks and not stored in PostgreSQL.

---

# Object Access

Files are uploaded and downloaded through **presigned URLs**.

- The API authorizes the request and issues a presigned URL.
- The client transfers the file directly to or from object storage.
- File bytes never pass through the API container.

A presigned URL is issued only after the same authorization and tenant checks that protect the owning Knowledge Object. An object that belongs to another organization is reported as not found (404), like every cross-organization resource.

Presigned URLs expire. Their lifetime is a setting defined by the implementing task.

The rule protects the API request path. Server-side processing that must read or write file content — AI decomposition (ADR-0009), document generation (ADR-0009), printable journal forms (ADR-0010) — runs in the background worker (ADR-0007), which accesses object storage directly.

---

# Stored Metadata

The database stores only metadata about a file:

- bucket
- key
- size
- MIME type
- SHA-256
- uploaded-by
- uploaded-at

How the SHA-256 is obtained and verified for direct uploads is decided by P11-001.

---

# Ports and Adapters

- The port `StorageContract` lives in `backend/core/contracts/`.
- The boto3 adapter lives in `backend/core/infrastructure/storage/`.
- The same adapter serves MinIO and Yandex Object Storage; connection parameters come from settings.
- Domain and application layers never import boto3. This is enforced by the architecture tests.

The existing placeholder in `backend/core/contracts/storage.py` is superseded. It is replaced by a port built around presigned access and file metadata. The port offers no physical deletion.

---

# External References

A document may point at an object in a bucket SafetyMAIN does not own, for example `complex-hr-docs` owned by `hr_form`.

Such objects are:

- read-only for SafetyMAIN;
- never copied into SafetyMAIN-owned buckets;
- fetched with a dedicated read-only credential, separate from the credential for SafetyMAIN-owned buckets.

SafetyMAIN records the bucket and key of an external reference; the owning system keeps its own key scheme (ADR-0008).

---

# Key Scheme

SafetyMAIN-owned objects use the key:

```text
{organization_id}/{aggregate}/{aggregate_id}/{version}/{filename}
```

- `organization_id` comes first, so the tenant boundary is visible in every key.
- `version` gives every version of a document its own objects; a new version never overwrites a previous one (Version Everything).
- Tenant isolation is enforced by authorization, not by the key prefix alone.

The key scheme does not apply to external references.

---

# Retention

- Objects referenced by an `archived` document are kept.
- Physical deletion is out of scope. This matches the platform rule that there are no destructive DELETE operations unless explicitly designed.

---

# Principles

- One file store for the whole platform.
- PostgreSQL keeps metadata; object storage keeps bytes.
- The API authorizes; object storage transfers.
- The tenant boundary comes first.
- Objects owned by other systems are referenced, never copied.
- Evidence is never physically deleted.

---

# Impact on Architecture Decision Freeze

The Architecture Decision Freeze §6 lists MinIO in the Hybrid Storage Model.

This ADR reads that entry as "S3-compatible object storage":

- MinIO remains the development implementation;
- production uses Yandex Object Storage through the same S3 API.

The other §6 entries (PostgreSQL, JSONB, pgvector, Redis) are unchanged.

Following the Freeze Change Policy, this reading takes effect after Architecture Review and approval of this ADR.

Impact analysis:

- Domain layer: no change; file metadata is plain data.
- Application layer: uses `StorageContract` only.
- Infrastructure layer: gains the boto3 adapter.
- Development: `docker-compose.yml` gains a MinIO service.
- Production: the environment gains credentials for SafetyMAIN-owned buckets and a separate read-only credential for external references.

---

# Consequences

- P11-001 introduces the storage port, the boto3 adapter, the MinIO development service, and the storage settings, and replaces the placeholder `backend/core/contracts/storage.py`.
- P11-001 adds `boto3` and `botocore` to the forbidden import prefixes in `tests/architecture/test_domain_dependencies.py`, `tests/architecture/test_application_dependencies.py`, and `tests/architecture/test_contract_dependencies.py`. Today these tests forbid `redis` and `minio` but not `boto3`.
- Every aggregate that carries files stores file metadata, not file content.
- Browsers reach the object storage endpoint directly. Bucket CORS and endpoint reachability become deployment concerns documented in `docs/infrastructure/ApplicationServerDeployment.md`.
- Physical deletion of objects requires a future ADR.

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0002 Knowledge Object Specification
- ADR-0005 Obligations Engine
- ADR-0007 Background Worker and Scheduling
- ADR-0008 HR Integration Contract
- ADR-0009 Knowledge Blocks and Document Assembly
- ADR-0010 Electronic Journals and Simple Electronic Signature

---

# Decision Summary

Files live in S3-compatible object storage.

PostgreSQL keeps only file metadata.

The API authorizes access; object storage transfers the bytes.

Objects owned by other systems are referenced, never copied, and evidence is never physically deleted.
