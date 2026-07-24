# ADR — Frontend UI Library

Status: Accepted  
Date: 2026-07-25  
Task: TASK-P9-002

## Context

SafetyMAIN needs an accessible, themeable, dense enterprise UI aligned with a custom Design System (teal/slate, IBM Plex, status language). Options considered: MUI, Ant Design, Radix/Headless, fully custom.

## Decision

Use **custom SafetyMAIN primitives** styled with **design tokens (CSS variables)**, with **Radix UI Slot** (and additional Radix primitives as needed later) for accessibility composition.

Icons: **Lucide React** (outline, matches Design System).

Business features must import `@/components/*`, never MUI/Ant/Radix directly (except within the shared component layer).

## Rationale

1. Design System is bespoke — heavy full kits fight token ownership.
2. Radix provides accessible primitives without imposing visual language.
3. Long-term customization for OHS workflows (dense registries, status badges) is simpler.
4. Avoids dual competing design languages.

## Consequences

- P9-003 must expand the shared catalog (inputs, dialog, drawer, DataGrid chrome).
- More upfront component work than adopting MUI wholesale.
- Storybook + a11y tests become mandatory for each primitive.
