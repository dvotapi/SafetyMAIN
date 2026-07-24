# Authentication Security Events

Status: Active  
Date: 2026-07-24  
Task: TASK-P6-003

Related documents:

- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
- [AdministrativeAuditLog.md](AdministrativeAuditLog.md)
- [AdminAuditAPI.md](../api/AdminAuditAPI.md)
- [SecurityEventInvestigation.md](SecurityEventInvestigation.md)
- [AuditEventIntegrity.md](AuditEventIntegrity.md)
- [SecurityOperationsArchitectureReview.md](SecurityOperationsArchitectureReview.md)

---

## 1. Purpose

Authentication Security Events record structured, immutable, taxonomy-backed outcomes of
login and refresh workflows.

Operators can distinguish:

- successful login;
- failed login;
- successful refresh;
- failed refresh;
- logout;
- refresh-token reuse (compromise response);
- administrative/session-wide revocation;

without exposing credentials, tokens, raw JWT data, or unnecessary identity information.

Recording is observational. It is not part of credential validation or token authorization.

---

## 2. Canonical Event Types

| Event type | Outcome | Significance | Producer owner |
|------------|---------|--------------|----------------|
| `authentication.login.succeeded` | SUCCESS | INFORMATIONAL | `AUTHENTICATION` |
| `authentication.login.failed` | FAILURE | MEDIUM | `AUTHENTICATION` |
| `authentication.refresh.succeeded` | SUCCESS | INFORMATIONAL | `AUTHENTICATION` |
| `authentication.refresh.failed` | FAILURE | MEDIUM | `AUTHENTICATION` |
| `authentication.logout.succeeded` | SUCCESS | INFORMATIONAL | `AUTHENTICATION` |
| `authentication.refresh.reused` | FAILURE | HIGH | `AUTHENTICATION` |
| `authentication.session.revoked` | SUCCESS | MEDIUM | `AUTHENTICATION` |

Subject domain for all authentication events: `SESSION`.

Persisted `AuditAction` values match these identifiers exactly. Free-form event names are
not permitted outside the taxonomy registry.

Additional session lifecycle events (logout, reuse, bulk revoke) are defined by
TASK-P7-002. See [RefreshTokenSessions.md](RefreshTokenSessions.md).

---

## 3. Taxonomy Fields

Each descriptor identifies:

- event name (`event_type`);
- category (`AUTHENTICATION`);
- subject domain (`SESSION`);
- producer owner (`AUTHENTICATION`);
- allowed outcomes (single outcome per event type);
- default security significance (registry metadata only);
- description.

Actor and organization are not mandatory taxonomy dimensions. Authentication failures may
occur before `SecurityContext` exists.

---

## 4. Safe Metadata

Allowlisted metadata keys used by authentication events:

| Key | Description |
|-----|-------------|
| `request_id` | Correlation ID from request middleware |
| `session_id` | Persistent refresh session UUID (internal audit only; not a token) |
| `revocation_reason` | Normalized reason when a session is revoked |
| `revoked_session_count` | Count for bulk revocation events |

| `client_ip` | Direct ASGI client address when available |
| `user_agent` | User-Agent header when available |
| `authentication_method` | Login method identifier (`password`) |

Optional string values are trimmed and truncated before persistence.

Persisted resource type is `SESSION`. Successful events set `resource_id` to the trusted
user UUID. Failed refresh events leave `resource_id` unset.

---

## 5. Prohibited Sensitive Data

Never persist or log:

- passwords;
- password hashes;
- access tokens;
- refresh tokens;
- complete authorization headers;
- JWT payloads;
- token signatures;
- authentication secrets;
- raw JWT library exception text;
- email addresses or submitted usernames as metadata.

---

## 6. Unknown-Actor Behavior

| Outcome | Actor user ID |
|---------|---------------|
| Login succeeded | Trusted authenticated user ID |
| Login failed (unknown email) | `None` |
| Login failed (known user, invalid password) | Known user ID |
| Login failed (inactive/forbidden user) | Known user ID |
| Refresh succeeded | Trusted subject after successful validation and issuance |
| Refresh failed | Always `None` (untrusted JWT data is never treated as actor) |

Organization ID is recorded only when already present in the authentication audit context.
Login/refresh workflows do not infer organization membership.

---

## 7. Normalized Failure Reasons

Failure reasons are stored in `AuditEvent.failure_code`.

Login:

```text
invalid_credentials
authentication_forbidden
```

Refresh:

```text
invalid_refresh_token
expired_refresh_token
invalid_token_type
invalid_token_claims
authentication_forbidden
```

Public HTTP error codes and messages remain unchanged. Refresh denials continue to map to
`401 invalid_refresh_token` at the API boundary regardless of the normalized audit reason.

---

## 8. Transaction and Persistence Failure Semantics

Authentication is the primary operation.

Both success and failure authentication events are persisted in a separate Unit of Work
transaction after the authentication decision.

If audit persistence fails:

- the authentication success or denial is preserved;
- the failure is logged with structured application logging;
- the client does not receive HTTP 500 solely because audit write failed;
- invalid credentials are not remapped to a different public error;
- security event metadata is not leaked to the client.

This differs from administrative mutation success auditing, which shares the business
transaction. Authentication handlers do not mutate administrative resources in the same
UoW as token issuance.

---

## 9. Layer Responsibilities

### API boundary

`backend/api/authentication_audit.py` extracts safe request metadata:

- request ID;
- direct client IP;
- user agent.

It must not read passwords, tokens, authorization headers, or request bodies into the
audit context. Forwarded IP headers are ignored unless an explicit trusted-proxy policy
exists.

### Application recorder

`AuthenticationSecurityEventRecorder`:

- resolves event definitions through the immutable taxonomy registry;
- builds immutable `AuditEvent` records;
- validates metadata against the allowlist;
- persists through the Unit of Work factory;
- does not depend on FastAPI request objects.

### Handlers

`AuthenticateUserHandler` and `RefreshAuthenticationHandler` call the recorder after the
authentication decision and before returning or re-raising the existing application
exception.

---

## 10. Examples

### Login success

```text
action: authentication.login.succeeded
outcome: SUCCESS
actor_user_id: <user uuid>
resource_type: SESSION
metadata: {request_id, client_ip?, user_agent?, authentication_method=password}
```

### Login failure (unknown account)

```text
action: authentication.login.failed
outcome: FAILURE
actor_user_id: null
failure_code: invalid_credentials
resource_type: SESSION
```

### Refresh failure (expired token)

```text
action: authentication.refresh.failed
outcome: FAILURE
actor_user_id: null
failure_code: expired_refresh_token
resource_type: SESSION
```

---

## 11. Operational Considerations

- Organization-scoped Admin Audit API listing requires
  `authorization_organization_id` or `target_organization_id` in scope. Authentication
  events without organization context are persisted but are not visible through the
  current tenant-scoped Audit API. Platform-level authentication event query remains
  future work.
- Investigation filters for taxonomy-backed authentication events are documented in
  [SecurityEventInvestigation.md](SecurityEventInvestigation.md).
- Authentication events receive the shared integrity hash chain at persistence time;
  see [AuditEventIntegrity.md](AuditEventIntegrity.md). Org-less auth events join the
  platform chain partition.
- Events provide a foundation for future monitoring, anomaly detection, lockout, and
  alerting. Those capabilities are out of scope for P6-003.
- Compatibility mode (`AUTH_ENFORCEMENT=false`) does not disable authentication endpoint
  event recording.
