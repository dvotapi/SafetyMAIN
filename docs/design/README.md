# SafetyMAIN Design System

Status: Active  
Date: 2026-07-25  
Task: [TASK-P9-001](../tasks/TASK-P9-001.md)

This Design System is the single visual, UX, and interaction contract for the SafetyMAIN frontend.

It does **not** ship React components or a running application. It defines the language that Product, UX, and Engineering share before implementation begins.

## Audience

| Role                 | Use                                                 |
| -------------------- | --------------------------------------------------- |
| Product              | Page templates, workflow language, navigation IA    |
| UX / Design          | Tokens, status language, components, accessibility  |
| Frontend Engineering | Architecture, dependency rules, token → CSS mapping |

## Document map

| Document                                           | Contents                                        |
| -------------------------------------------------- | ----------------------------------------------- |
| [Principles.md](Principles.md)                     | Design philosophy and non-negotiables           |
| [Tokens.md](Tokens.md)                             | Typography, spacing, sizing, color, elevation   |
| [Iconography.md](Iconography.md)                   | Icon style, sizes, domain icon map              |
| [StatusLanguage.md](StatusLanguage.md)             | Unified lifecycle / operational statuses        |
| [RussianUICopy.md](RussianUICopy.md)               | Locked Russian frontend terminology and copy    |
| [Layout.md](Layout.md)                             | Shell, panels, drawers, modals, sticky regions  |
| [Navigation.md](Navigation.md)                     | Primary and nested navigation                   |
| [PageTemplates.md](PageTemplates.md)               | Reusable page types and Object Page             |
| [WorkflowPattern.md](WorkflowPattern.md)           | Lifecycle-oriented workflow UI                  |
| [DashboardPattern.md](DashboardPattern.md)         | Attention-first dashboards                      |
| [RegistryPattern.md](RegistryPattern.md)           | Large-data registries / grids                   |
| [Forms.md](Forms.md)                               | Form layout, validation, progressive disclosure |
| [TimelineAndActivity.md](TimelineAndActivity.md)   | Timeline and activity feed                      |
| [ComponentCatalog.md](ComponentCatalog.md)         | Shared component inventory                      |
| [ObjectRelationships.md](ObjectRelationships.md)   | Linked-object navigation                        |
| [Responsive.md](Responsive.md)                     | Desktop / tablet / mobile strategy              |
| [Accessibility.md](Accessibility.md)               | WCAG AA guidance                                |
| [Motion.md](Motion.md)                             | Motion principles                               |
| [Themes.md](Themes.md)                             | Light, Dark, high-contrast readiness            |
| [FrontendArchitecture.md](FrontendArchitecture.md) | Folder structure and dependency rules           |

## Related platform docs

- [UbiquitousLanguage.md](../domain/UbiquitousLanguage.md) — domain terms for UI copy
- [LifecycleRules.md](../domain/LifecycleRules.md) — authoritative status transitions
- [SafetyAuthorization.md](../architecture/SafetyAuthorization.md) — RBAC surface the UI must respect

## Implementation status

| Layer                                     | Status                                                   |
| ----------------------------------------- | -------------------------------------------------------- |
| Design documentation                      | **Implemented** (P9-001)                                 |
| Design tokens as code                     | **Implemented** — [TASK-P9-002](../tasks/TASK-P9-002.md) |
| Shared React primitives (bootstrap set)   | **Implemented** — [TASK-P9-002](../tasks/TASK-P9-002.md) |
| Full component library / business screens | **Deferred**                                             |

## Non-goals (P9-001)

No production UI, React components, routing, auth wiring, API clients, or CRUD screens.
