# Frontend Testing

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-002

## Stack

| Layer | Tool |
|-------|------|
| Unit / component | Vitest + React Testing Library + jest-dom |
| Accessibility | vitest-axe (+ Storybook a11y addon) |
| E2E smoke | Playwright |
| API mocks (dev/test) | MSW handlers under `src/test/msw` (not production) |
| Architecture | dependency-cruiser |

## Commands

```bash
npm run test
npm run test:e2e   # run after `npm run build` (config starts `npm run start`)
npm run build-storybook
```

## Coverage goals (bootstrap)

Theme resolution, StatusBadge semantics, Button, Alert a11y, AppShell landmarks, API error normalization, env validation.

## Known limitations

Automated axe checks cover bootstrap components only — not a formal WCAG audit.
