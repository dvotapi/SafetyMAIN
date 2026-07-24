# Forms

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Tokens.md](Tokens.md) · [PageTemplates.md](PageTemplates.md) · [Accessibility.md](Accessibility.md)

---

## 1. Field layout

| Rule | Detail |
|------|--------|
| Label position | Top-aligned labels (not left) for scalability and localization |
| Width | Single column default; two-column only for short paired fields on `md+` |
| Gap | `space.4` between fields; `space.6` between sections |
| Required | Asterisk + `required` in accessible name; never color-only |
| Optional | Omit “optional” unless most fields are required |

## 2. Validation

1. Validate on blur for fields; on submit for the form.
2. Block submit when client-side requireds fail; map server 422 to field errors.
3. Error text uses `color.danger.fg` beneath the field; input border danger.
4. Summary alert at top when ≥ 3 errors or cross-field rules fail.
5. Preserve user input on failure.

## 3. Helper text

- Helper: `color.text.muted`, always associated via `aria-describedby`.
- Error replaces helper for that field while invalid.
- Examples in helper, not placeholder-as-label.

## 4. Section grouping

Use section titles (`text.sectionTitle`) + optional description.  
Group by mental model (Identity, Classification, Scope, Ownership) — not by API payload shape.

## 5. Progressive disclosure

- Advanced / rare fields behind “Show advanced”.
- Dependent fields appear when parent value requires them.
- Wizards split long creates across steps with per-step validation.

## 6. Autosave

| Context | Behavior |
|---------|----------|
| Long Object edit | Optional autosave draft with explicit “Saved” indicator |
| Lifecycle commands | **Never** autosave — explicit confirm |
| Wizards | Save draft action; autosave if implemented must be labeled |

Show last-saved timestamp; conflict (409) opens version conflict dialog.

## 7. Command placement

- Primary submit / lifecycle CTA: right side of sticky action bar.
- Secondary: Cancel / Back left or secondary style.
- Destructive: isolated, never adjacent lookalike to primary.

## 8. Error presentation

| Level | UI |
|-------|-----|
| Field | Inline |
| Form | Alert banner |
| Permission | Toast or banner; no fake success |
| Conflict | Dialog: reload vs overwrite discouraged — prefer reload |

## 9. Read-only mode

Object Pages default to read view; edit enters form mode or drawer. Lifecycle actions remain available without entering full edit when they are dedicated commands.
