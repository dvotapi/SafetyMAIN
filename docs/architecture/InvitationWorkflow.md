# Invitation Workflow

SafetyMAIN invitation workflow lets administrators issue single-use organization invitations and lets authenticated users accept them to obtain membership.

## Model

Invitations store organization, normalized invitee email, role, persisted lifecycle status, token hash, expiration, audit timestamps, and creator user ID. Plaintext tokens are never persisted.

## Lifecycle

Persisted statuses: `PENDING`, `ACCEPTED`, `REVOKED`. Expiration is evaluated dynamically: pending invitations with `expires_at <= now` are treated as effectively `EXPIRED` in APIs and lifecycle checks while persisted status remains `PENDING`.

## Token Security

Tokens are generated with `secrets.token_urlsafe(32)` and stored as SHA-256 hashes. Verification uses `secrets.compare_digest`. Tokens are returned only on create and reissue.

## Acceptance

Acceptance requires a valid access token and matching authenticated user email. User self-registration during acceptance is not supported; invitees must already exist. Membership is created or inactive membership is reactivated atomically with invitation acceptance.

## Authorization

Admin routes use `invitation:read` and `invitation:write`. Authorization organization comes from `TenantContext`; target organization comes from invitation data.

## Limitations

- No email delivery
- No invitation for users without existing accounts
- No background expiration job
