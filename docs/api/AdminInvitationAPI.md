# Admin Invitation API

Base path: `/api/v1/admin/invitations`

Requires Bearer JWT and `X-Organization-ID` authorization context.

| Method | Path | Permission |
|---|---|---|
| POST | `/` | `invitation:write` |
| GET | `/` | `invitation:read` |
| GET | `/{invitation_id}` | `invitation:read` |
| POST | `/{invitation_id}/revoke` | `invitation:write` |
| POST | `/{invitation_id}/reissue` | `invitation:write` |

Create and reissue responses include a one-time plaintext `token`.
