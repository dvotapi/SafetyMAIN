# TASK-P11-007 — Notifications: In-App Inbox and Email

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-006

---

## Goal

Deliver obligation warnings to the right people, on time, without noise:
an in-app inbox with a bell counter, transactional email through SMTP, a
recipient policy (employee → line manager → safety specialist), one message
per threshold, and a weekly digest for managers.

---

## Context

- P11-006 emits `ObligationDueSoon(threshold)`, `ObligationOverdue`,
  `ObligationCreated`, `ObligationCompleted` and stores
  `notified_thresholds` per obligation.
- `backend/core/infrastructure/messaging/` is empty. No SMTP settings exist.
- Decision: recipients are the employee's line manager
  (`Employee.manager_employee_id` → linked user) and the occupational-safety
  specialist (organisation setting `safety_specialist_employee_id`); the
  employee themselves receives in-app + email when they have an account.
- Corporate mailboxes exist for ИТР; blue-collar employees may lack one —
  in-app is the fallback and the UI shows "email не настроен".

---

## Scope

### 1. Ports and adapters

- `EmailSenderContract.send(message: EmailMessage) -> DeliveryResult` in
  `core/contracts/`; adapter `SmtpEmailSender` (smtplib, STARTTLS/SSL, auth)
  and `InMemoryEmailSender` for tests; Mailpit service in
  `docker-compose.yml`.
- Settings: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`,
  `SMTP_USE_TLS`, `EMAIL_FROM`, `EMAIL_REPLY_TO`, `NOTIFICATIONS_ENABLED`,
  `APP_PUBLIC_URL` (for links). Production validation: all required when
  enabled.

### 2. Notification model

- `notifications`: id, org, `recipient_user_id`, `recipient_employee_id`,
  `channel` (`in_app | email`), `kind` (`due_soon | overdue | created |
  completed | digest | signature_pending`), `obligation_id` (nullable for
  digest), `threshold_days`, `title_ru`, `body_md`, `link`, `status`
  (`queued | sent | failed | read`), `dedupe_key`, `created_at`, `sent_at`,
  `read_at`, `error`.
- `notification_preferences` (per user): email on/off per kind, digest
  weekday; defaults from org settings.
- Recipient policy service: given an event → list of (user, channel)
  according to the decision above and to preferences; employee obligations
  without a linked user go to the manager only.

### 3. Jobs

- Event handlers enqueue notifications (idempotent via `dedupe_key` =
  event + obligation + threshold + recipient + channel).
- `dispatch_notifications` (every 5 min): sends `queued` email in batches
  with retry/backoff; marks failures with the SMTP error; never blocks the
  API.
- `send_weekly_digest` (Monday 08:00 local, org timezone setting): per
  manager — their team's overdue and next-30-days obligations; per safety
  specialist — the organisation summary; skipped when empty.
- `signature_pending` reminders for journal entries awaiting ПЭП older than
  N days (uses P11-005 data).

### 4. Templates

- Russian email templates (subject + text + HTML) as versioned files under
  `backend/core/application/notification_templates/`, rendered with Jinja2;
  copy terminology from `docs/design/RussianUICopy.md`. Links use
  `APP_PUBLIC_URL`. Content never includes personal identifiers beyond name
  and position.

### 5. API

```text
GET   /api/v1/me/notifications          (unread first, pagination)
GET   /api/v1/me/notifications/unread-count
POST  /api/v1/me/notifications/{id}/read ; POST .../read-all
GET/PATCH /api/v1/me/notification-preferences
GET   /api/v1/admin/notifications        (delivery log, filters, resend)
POST  /api/v1/admin/notifications/{id}/resend
```

Permissions: `notification:read_self`, `notification:admin`. Audit:
`notification.sent | failed | resent` (email only; in-app reads are not
audited).

### 6. Frontend

- Bell in the app shell with unread count (polling interval from settings;
  no websockets), dropdown with latest, page `/me/notifications`.
- Preferences page.
- Dashboard widget "Ближайшие сроки" (Overview page) using
  `/obligations/summary` and the top-N list — pattern
  `docs/design/DashboardPattern.md`.
- Admin delivery log with resend.

### 7. Documentation

`docs/architecture/Notifications.md`, `docs/api/NotificationsAPI.md`,
runbook section for SMTP configuration and Mailpit, `CLAUDE.md`.

---

## Acceptance Criteria

- An obligation crossing the 30-day threshold produces exactly one in-app
  and one email notification per recipient, even when evaluation runs
  several times (dedupe test).
- Recipient policy tests cover: employee with account, employee without
  account, missing manager (falls back to safety specialist), preferences
  disabling email.
- SMTP failure leaves the notification `failed` with the error and is
  retried; the API remains unaffected (test with a failing sender).
- Weekly digest renders and is sent only when there is content.
- Bell count and inbox work; `npm run verify`; E2E: mark as read.
- Mailpit shows correctly rendered Russian emails with working links.

---

## Non-Goals

- Telegram/SMS/push (design the channel enum to allow later).
- Real-time delivery (websockets).
- Per-department escalation chains beyond manager → specialist.

---

## Verification

Unit tests for policy, dedupe, templates (snapshot); job tests with fake
sender and clock; frontend tests; manual Mailpit check.

---

## Suggested implementation phases

1. Email port/adapters/settings/Mailpit.
2. Notification model + preferences + policy + migration.
3. Event handlers + dispatch + digest + reminders.
4. API + docs.
5. Frontend bell, inbox, preferences, dashboard widget, admin log.
