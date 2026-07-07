# ADR-0004 — Compliance Rules Engine (CRE)

**Status:** Accepted

**Date:** 2026-07-07

**Authors:** SafetyMAIN Architecture Team

---

# Context

SafetyMAIN manages compliance obligations originating from legislation, industrial safety regulations, occupational safety requirements, internal corporate standards and enterprise-specific procedures.

Business behavior must not be hardcoded.

The platform requires a configurable and versioned rules engine capable of evaluating compliance obligations and triggering platform actions.

---

# Decision

SafetyMAIN adopts a Compliance Rules Engine (CRE).

Business behavior shall be defined by declarative Compliance Rules instead of application source code whenever technically feasible.

Compliance Rules are first-class Knowledge Objects.

---

# Compliance Rule Structure

Every Rule shall contain:

- Identity
- Version
- Status
- Scope
- Trigger
- Conditions
- Actions
- Priority
- Effective Date
- Expiration Date
- Source
- Related Regulations
- Related Knowledge Objects
- Audit History
- AI Summary

---

# Trigger Types

Rules may be triggered by:

- Entity creation
- Entity update
- Scheduled evaluation
- Date expiration
- Event reception
- User action
- AI recommendation

---

# Supported Actions

Rules may:

- Create Tasks
- Generate Notifications
- Create Knowledge Objects
- Generate Documents
- Request Review
- Escalate Issues
- Update Dashboards
- Trigger AI Analysis
- Trigger Workflows

---

# Principles

- Rules over hardcoded business logic
- Versioned rules
- Explainable decisions
- Metadata-driven execution
- AI-assisted recommendations
- Human approval where required

---

# Benefits

- Configurable compliance logic
- Reduced code changes
- Better traceability
- Easier regulatory updates
- Enterprise scalability
- Full auditability

---

# Consequences

Business workflows shall be implemented using Compliance Rules whenever possible.

Direct implementation of business logic in application code should be minimized.

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0002 Knowledge Object Specification
- ADR-0003 Metadata Engine
- ADR-0005 Event Engine (planned)
- ADR-0006 Knowledge Graph (planned)

---

# Decision Summary

SafetyMAIN executes business behavior through versioned Compliance Rules.

Rules are Knowledge Objects and participate in versioning, auditing, AI analysis and the Knowledge Graph.
