# TASK-P10-002 — Fix missing spacing between icon and label in `Button`

## Origin

Found during the production smoke test of the P10-001 deployment
(`a611dd9`) on `sm.complex-services.ru`. The owner flagged the header as
looking visually broken — icons pressed against text, elements crowded
together — after logging in as `Platform Admin`.

## Problem

Every `Button` instance that renders multiple children (an icon plus a
label, an avatar plus a name) showed no gap between them: `OrganizationSwitcher`
("🏢Complex Services") and `UserMenu` ("PAPlatform Admin") in the top nav
were the visible cases, but the defect is in the shared primitive, not in
either call site.

## Root cause

`frontend/src/components/primitives/Button.tsx` wrapped all non-loading
children in one plain `<span>`:

```tsx
<span className={cx(loading && styles.loadingContent)}>{children}</span>
```

`Button.module.css` puts `display: inline-flex; gap: var(--sm-space-2)` on
the `<button>` itself, expecting its children to be separate flex items.
Instead, that single wrapper `<span>` (no class when not loading, so
`display: block`) became the button's *only* flex child — the gap had
nothing to apply between. Everything inside the span (icon, avatar, text)
rendered as plain inline content with zero spacing.

Confirmed live on production via `getComputedStyle`: the wrapper span had
`display: "block"`, `gap: "normal"`.

Pre-existing bug, not introduced by P10-001: `git log -p -L` on that line
shows the wrapper was added in `03817cc` (P9-002, app shell bootstrap,
2026-07-25). P10-001 only touched the loading-spinner label text
("Loading" → "Загрузка") on an adjacent line. It simply hadn't been
noticed before this smoke test.

## Fix

`frontend/src/components/primitives/Button.tsx`: only wrap children in a
span while `loading` (needed there so `visibility: hidden` can hide the
label under the spinner without unmounting it). When not loading, render
`children` directly as the button's flex children, so `gap` applies as
designed.

```tsx
{loading ? (
  <>
    <span className={styles.loadingSpinner} aria-hidden>
      <Spinner className={styles.buttonSpinner} label="Загрузка" />
    </span>
    <span className={styles.loadingContent}>{children}</span>
  </>
) : (
  children
)}
```

No CSS changed — `.button`'s existing `display: inline-flex; gap` now
reaches the real children.

## Scope

Single file, `frontend/src/components/primitives/Button.tsx`. No API,
schema, or unrelated component changes. Affects every `Button` in the app
that renders more than one child (icon+label buttons, `OrganizationSwitcher`,
`UserMenu`, any button with a leading/trailing icon) — all of them get the
intended spacing back, none regress since the loading state path is
unchanged.

## Verification

- `npm run typecheck` — clean.
- `npm run lint` — clean (`--max-warnings=0`).
- Local repro (dev server, real design tokens): rendered the old wrapped-span
  markup next to the fixed direct-children markup side by side —
  `PAPlatform Admin` (no gap) vs `PA Platform Admin` (8px gap, matches
  `--sm-space-2`).
- Not yet re-verified against the production build/screenshot — the fix has
  not been deployed. See Remaining actions.

## Remaining actions

- Deploy to `sm.complex-services.ru` (rebuild `safetymain-frontend`, no
  migration needed) and re-run the header visual check from the browser.
- Optional: add a Storybook/unit regression check for multi-child `Button`
  spacing so this class of bug fails CI instead of requiring a manual
  smoke test to catch.
