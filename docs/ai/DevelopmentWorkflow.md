# Development Workflow

## Purpose

This document defines the mandatory development workflow for SafetyMAIN.

Every implementation task must follow this workflow.

The objective is:

- protect architecture quality;
- minimize unnecessary AI context usage;
- keep implementation predictable;
- make work reproducible across humans and AI agents;
- reduce implementation risk.

Skipping workflow stages is not allowed unless explicitly approved.

---

# Phase 0 — Architecture

Owner:

- Human
- ChatGPT

Goal:

Design the solution.

Activities:

- discuss requirements;
- define scope;
- identify affected domains;
- define architecture;
- identify risks;
- identify non-goals;
- define acceptance criteria.

Output:

- approved architecture
- approved implementation approach

No code is written during this phase.

---

# Phase 1 — Task Specification

Owner:

- Human
- ChatGPT

Goal:

Create the implementation contract.

Activities:

- create TASK document;
- define scope;
- define acceptance criteria;
- define verification;
- define non-goals.

Output:

```
docs/tasks/TASK-XXXX.md
```

This document becomes the implementation contract.

---

# Phase 2 — Planning

Owner:

- Cursor (Plan Mode)

Goal:

Understand the repository.

Activities:

- read AI_CONTEXT.md;
- read TASK;
- inspect only relevant documentation;
- inspect only relevant source files;
- inspect closest existing implementation.

Do not modify code.

Output:

Approved implementation plan containing:

- Goal
- Affected files
- Architecture boundaries
- Backend contract
- Implementation phases
- Verification strategy
- Risks
- Known limitations

---

# Phase 3 — Plan Review

Owner:

- Cursor
- Human
- ChatGPT

Goal:

Challenge the implementation plan.

Review:

- unnecessary scope;
- architecture violations;
- backend contract mismatches;
- duplicated work;
- risky assumptions;
- missing acceptance criteria.

Possible decisions:

- APPROVE
- APPROVE WITH CORRECTIONS
- REJECT

Only an approved plan may enter implementation.

---

# Phase 4 — Implementation

Owner:

- Cursor (Agent Mode)

Implementation is performed one phase at a time.

Example:

Phase 1

↓

Review

↓

Phase 2

↓

Review

↓

Phase 3

Large tasks must never be implemented in a single execution.

Each implementation phase must define:

- scope;
- excluded work;
- verification.

---

# Phase 5 — Self Review

Owner:

- Cursor

Before requesting human review Cursor must verify:

□ implementation matches approved phase

□ no unrelated changes

□ no scope creep

□ no TODO

□ no FIXME

□ no invented API

□ no invented permissions

□ architecture respected

□ feature boundaries respected

□ backend contract respected

□ focused tests pass

□ typecheck passes

Cursor must not declare a phase complete until this checklist passes.

---

# Phase 6 — Independent Review

Owner:

- Cursor
- ChatGPT

Review categories:

## Contract

- DTO
- API
- Permissions
- Lifecycle
- Validation

## Architecture

- DDD
- Feature boundaries
- Shared components
- Dependency rules

## Implementation

- Code quality
- Tests
- Edge cases
- Dead code
- Unnecessary abstractions

Findings are classified as:

- BLOCKER
- IMPORTANT
- MINOR
- NO ISSUE

Decision:

- APPROVE
- APPROVE WITH MINOR CORRECTIONS
- REJECT

---

# Phase 7 — Corrections

Owner:

- Cursor

Only review findings are fixed.

No new functionality may be added.

After corrections:

- rerun focused verification;
- rerun review.

---

# Phase 8 — Acceptance

A phase is complete only when:

- review decision is APPROVE
or
- APPROVE WITH MINOR CORRECTIONS

REJECT always requires another correction cycle.

---

# Phase 9 — Next Phase

Only after acceptance:

Cursor may start the next implementation phase.

---

# Phase 10 — Task Completion

Owner:

- Cursor
- Human

Activities:

- final verification;
- update documentation;
- update TASK completion report;
- verify acceptance criteria;
- ensure no known blockers remain.

Output:

TASK marked completed.

---

# Definition of Done

A task is complete only when:

- all Acceptance Criteria satisfied;
- all required tests pass;
- architecture documentation updated;
- implementation documentation updated;
- verification completed;
- review approved;
- no BLOCKER findings remain.

---

# Context Rules

Cursor should always read:

1. AI_CONTEXT.md

2. Current TASK

3. Relevant architecture documents

4. Closest existing implementation

Cursor must never scan the entire repository unless explicitly required.

---

# Context Discipline

One chat = one logical phase.

Recommended:

Architecture

↓

Planning

↓

Phase 1

↓

Review

↓

Phase 2

↓

Review

↓

...

Never continue implementation after a phase has been accepted.

Open a new chat for each implementation phase.

---

# AI Responsibilities

## ChatGPT

Responsible for:

- architecture;
- design;
- task specification;
- workflow improvement;
- architectural review.

## Cursor Plan

Responsible for:

- repository analysis;
- implementation planning.

## Cursor Agent

Responsible for:

- implementation;
- tests;
- documentation updates.

## Cursor Review

Responsible for:

- implementation review;
- contract validation;
- architecture validation.

---

# Core Principle

Architecture is decided before implementation.

Implementation is approved before the next phase begins.

Every phase must be reproducible.

No AI agent should invent architecture during implementation.