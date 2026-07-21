# Invitation Acceptance API

Path: `POST /api/v1/invitations/accept`

Requires Bearer JWT. Does not require membership in the target organization.

Request:

```json
{
  "token": "<invitation-token>"
}
```

The authenticated user's email must match the invitation email.
