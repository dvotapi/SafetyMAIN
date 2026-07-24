# Refresh Token Sessions

Status: Active  
Date: 2026-07-24  
Task: TASK-P7-002

Related documents:

- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [AuthenticationSecurityEvents.md](AuthenticationSecurityEvents.md)
- [PersistentIdentityStores.md](PersistentIdentityStores.md)
- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
- [SecurityOperationsArchitectureReview.md](SecurityOperationsArchitectureReview.md)

---

## 1. Threat Model

Refresh JWTs are bearer credentials. Signature validity alone is insufficient:

| Threat | Mitigation |
|--------|------------|
| Stolen refresh token | Logout / admin revoke / user deactivation terminate the persistent session |
| Token replay after rotation | Reuse of a prior `jti` revokes the entire session family |
| Concurrent double-spend | Atomic `UPDATE ... WHERE current_token_id_hash = expected` / `FOR UPDATE` |
| Raw token leakage from DB | Persist only SHA-256 of `jti` (never the JWT) |
| Session existence oracle via logout | Invalid and already-rotated tokens return the same success |
| Stale role authority in long-lived refresh | Membership/role authority remains PostgreSQL-backed; refresh does not embed roles |

Access tokens remain short-lived and are **not** revoked by this design.

---

## 2. Session Entity and Token Family

Domain entity: `RefreshTokenSession`  
(`backend/core/domain/entities/refresh_token_session.py`)

| Field | Meaning |
|-------|---------|
| `session_id` | Stable session identifier (also JWT claim) |
| `family_id` | Stable family across rotations; unique in DB |
| `current_token_id_hash` | SHA-256 hex of current refresh `jti` |
| `previous_token_id_hash` | Prior hash retained for replay diagnosis |
| `expires_at` | Sliding expiry (advanced on rotation, capped by absolute) |
| `absolute_expires_at` | Hard ceiling; never extended by rotation |
| `revoked_at` / `revocation_reason` | Revocation state |

A session represents one refresh-token **family**, not the encoded JWT.

---

## 3. JWT Claims (Refresh)

Required after cryptographic validation:

```text
sub, jti, session_id, family_id, typ=refresh, iat, exp, iss
```

- `jti` changes on every successful rotation
- `session_id` and `family_id` remain stable
- Claims are trusted only after JWT validation succeeds

Issuer: `JwtTokenService` (`backend/core/infrastructure/auth/jwt_token_service.py`).

---

## 4. JTI Hashing

`hash_refresh_token_jti` (`backend/core/domain/services/refresh_token_jti_hasher.py`):

- SHA-256 over the raw `jti` string
- lowercase hex (64 chars)
- never Python `hash()`
- never log or persist raw `jti`
- do not hash the full JWT as the session identifier

---

## 5. Login Session Creation

`AuthenticateUserHandler`:

1. verify credentials and active user
2. create `session_id`, `family_id`, random `jti`
3. issue access + refresh JWTs with session claims
4. persist session (`current_token_id_hash`) and commit
5. record `authentication.login.succeeded`

If persistence fails, login fails and no usable refresh token is returned to the client.

---

## 6. Refresh Validation Order

`RefreshAuthenticationHandler`:

1. cryptographically validate refresh JWT
2. validate issuer, expiry, `typ`, required claims
3. `get_for_update(session_id)`
4. session exists; subject and family match
5. not revoked; sliding and absolute expiry OK
6. presented `jti` hash equals `current_token_id_hash`
7. issue next token pair, then atomic rotate
8. commit; record `authentication.refresh.succeeded`

On `jti` mismatch for an otherwise valid session: revoke family as reuse, record
`authentication.refresh.reused`, return normalized `invalid_refresh_token`.

---

## 7. Rotation and Transaction Boundaries

Sequence (issue-then-rotate-then-commit):

1. compute next expiry (`min(now + sliding, absolute)`)
2. generate new `jti` and issue JWTs
3. conditional rotate of stored hash
4. commit UoW

If rotate fails, raise `refresh_rotation_conflict` and do not return tokens.  
Repositories never commit independently; handlers own the Unit of Work.

---

## 8. Replay, Logout, Deactivation

| Action | Behavior |
|--------|----------|
| Replay | Revoke session with `token_reuse_detected` |
| Logout `POST /api/v1/auth/logout` | Revoke only if presented `jti` is current; always 204 |
| User deactivation | `revoke_all_for_user(..., USER_DEACTIVATED)` in the same admin transaction |

Membership/role changes do **not** auto-revoke sessions; authorization re-resolves from PostgreSQL.

---

## 9. Expiration Policy

Configuration (`AppSettings`):

| Setting | Default | Rule |
|---------|---------|------|
| `jwt_refresh_token_ttl_seconds` | 7 days | sliding lifetime; must be > 0 |
| `jwt_refresh_absolute_ttl_seconds` | 90 days | absolute lifetime ≥ sliding |
| `refresh_token_rotation_enabled` | `true` | must be enabled; no silent downgrade |

Expired sessions cannot refresh. Absolute expiry cannot be extended by rotation.

---

## 10. Failure Normalization

Public refresh failures always map to `401` + `invalid_refresh_token`.

Internal reasons include:

```text
session_not_found, session_revoked, session_expired,
session_subject_mismatch, session_family_mismatch,
refresh_token_reuse_detected, refresh_rotation_conflict
```

`TokenValidationError.reason` covers JWT/crypto failures only.

---

## 11. Security Events

| Event | Notes |
|-------|-------|
| `authentication.logout.succeeded` | Logout path (including idempotent no-ops) |
| `authentication.refresh.reused` | Replay compromise response |
| `authentication.session.revoked` | Bulk revocation (e.g. deactivation) |

Safe metadata may include `session_id`, `revocation_reason`, `revoked_session_count`,
`request_id`, IP, user-agent. Never include raw `jti`, hashes, or JWTs.

---

## 12. Retention and Cleanup

| State | Retention |
|-------|-----------|
| Active | Until expiry or revocation |
| Expired / revoked | Short investigation window |
| Replay-compromised | At least as long as other revoked sessions |

Operational cleanup: `scripts/cleanup_refresh_sessions.py` (`--dry-run`, retention days).  
Never prints token hashes. Not invoked from request handlers.

---

## 13. Client Requirements

1. Send current refresh token
2. Receive new access + refresh pair
3. Atomically replace stored refresh token
4. Never reuse an older refresh token
5. Treat refresh failure as requiring re-authentication

No grace period for previous tokens.

---

## 14. Known Limitations

- Access tokens remain valid until their short TTL after logout/deactivation
- No public session-listing API
- In-memory refresh repository approximates concurrency for unit tests only
- Production requires PostgreSQL-backed Unit of Work; no silent in-memory fallback
