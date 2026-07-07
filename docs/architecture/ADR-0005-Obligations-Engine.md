# ADR-0005 — Obligations Engine

**Status:** Accepted

**Date:** 2026-07-07

**Authors:** SafetyMAIN Architecture Team

---

# Context

Compliance is not achieved by storing documents.

Compliance is achieved by fulfilling obligations.

Regulations, industrial safety expertise reports, licenses, permits, internal procedures and corporate policies all create obligations that must be monitored until completion.

Traditional document management systems do not manage obligations directly.

SafetyMAIN adopts an obligation-centric compliance model.

---

# Decision

SafetyMAIN introduces the Obligations Engine.

Obligations become first-class Knowledge Objects.

Every obligation has its own lifecycle and is continuously monitored until fulfilled or cancelled.

---

# Obligation Sources

Obligations may originate from:

- Laws
- Regulations
- Industrial Safety Expertise (EPB)
- Blasting Permits
- Licenses
- Internal Standards
- Corporate Policies
- Audit Findings
- Risk Assessments
- AI Recommendations
- User Decisions

---

# Obligation Structure

Every Obligation shall contain:

- UUID
- Title
- Description
- Source
- Related Regulation
- Related Knowledge Objects
- Responsible Person
- Responsible Department
- Due Date
- Priority
- Risk Level
- Current Status
- Evidence
- Completion Date
- Version
- Audit History
- AI Summary

---

# Obligation Lifecycle

Draft

↓

Active

↓

In Progress

↓

Completed

or

Cancelled

or

Overdue

---

# Monitoring

The platform continuously evaluates:

- approaching deadlines
- overdue obligations
- missing evidence
- blocked obligations
- dependencies
- regulatory changes

---

# Supported Actions

The engine may:

- Create Tasks
- Send Notifications
- Escalate Issues
- Trigger Reviews
- Generate Reports
- Update Dashboards
- Launch AI Analysis
- Generate Compliance Documents

---

# Principles

- Every obligation is traceable.
- Every obligation has an owner.
- Every obligation has evidence.
- Every obligation has a lifecycle.
- Every obligation is auditable.
- Every obligation is searchable.
- Every obligation participates in the Knowledge Graph.

---

# Benefits

- Complete compliance visibility
- Unified compliance management
- Automatic deadline monitoring
- Reduced regulatory risk
- Full traceability
- AI-assisted compliance

---

# Consequences

Future modules shall create and manage obligations instead of implementing isolated reminder mechanisms.

Reminder systems become implementations of the Obligations Engine.

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0002 Knowledge Object Specification
- ADR-0003 Metadata Engine
- ADR-0004 Compliance Rules Engine
- ADR-0006 Event Engine (planned)
- ADR-0007 Knowledge Graph (planned)

---

# Decision Summary

SafetyMAIN manages enterprise obligations rather than documents.

Documents are evidence.

Obligations are the real business objects.
