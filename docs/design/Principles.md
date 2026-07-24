# Design Principles

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [README.md](README.md) · [Tokens.md](Tokens.md) · [Accessibility.md](Accessibility.md)

---

## 1. Purpose

SafetyMAIN is an operational OHS platform. Users make decisions under time pressure, often with legal and human safety consequences. The UI must reduce ambiguity, surface the next correct action, and keep records trustworthy.

## 2. Core principles

### Clarity

- Prefer plain language aligned with [Ubiquitous Language](../domain/UbiquitousLanguage.md).
- One primary action per view region.
- Status and risk severity must be readable without relying on color alone.

### Consistency

- Same object types use the same Object Page, StatusBadge, and Timeline patterns.
- Tokens — never ad-hoc hex values — drive all color, space, type, and elevation.
- Interaction patterns (save, submit, confirm destructive) are identical across modules.

### Accessibility

- Target WCAG 2.2 AA where practical (see [Accessibility.md](Accessibility.md)).
- Keyboard parity for all primary workflows.
- Touch targets meet field-use minimums on tablet/mobile.

### Workflow orientation

- Screens express **lifecycle**, not CRUD.
- Primary CTA is the next valid domain transition (Plan, Approve, Verify…), not “Edit”.
- Blocked states explain *why* and what is missing.

### Information hierarchy

- Brand / product identity is clear in the shell; content hierarchy starts with object title + status.
- Critical alerts and overdue items outrank decorative metrics.
- Dense registries remain scannable; detail pages remain readable.

### Enterprise scalability

- Navigation and registries must absorb new domains (Inspection, Incident, Training…) without redesign.
- Saved views, filters, and column config are first-class for power users.
- Multi-tenant awareness is structural (org switcher, no cross-tenant leakage cues).

### Minimal cognitive load

- Hide advanced fields behind progressive disclosure.
- Prefer progressive forms and wizards for multi-step creation.
- Avoid ornament, competing accent colors, and non-functional motion.

## 3. Visual character

| Attribute | Direction |
|-----------|-----------|
| Tone | Confident, precise, operational |
| Density | Comfortable on Object Pages; compact available in Registries |
| Decoration | Minimal — no ornamental gradients as primary content |
| Metaphor | Control room / flight deck clarity, not consumer marketing |

### Avoid

- Legacy “grey box + blue link” enterprise look
- Decorative glassmorphism, neon glows, and marketing-landing motifs
- Purple-gradient “AI product” defaults
- Warm cream + terracotta brochure aesthetics as the product chrome
- Broadsheet / newspaper column layouts for operational screens

## 4. Decision tests

Before shipping a new pattern, answer:

1. Can a supervisor understand status and next action in under 5 seconds?
2. Does this reuse an existing template/component?
3. Would color-blind users still distinguish severity/status?
4. Does this work at registry scale (thousands of rows)?
5. Does copy use ubiquitous language?

If any answer is no, revise before inventing a one-off UI.
