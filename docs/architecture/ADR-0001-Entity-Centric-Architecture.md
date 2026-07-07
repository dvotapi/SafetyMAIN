# ADR-0001 — Entity-Centric Architecture

**Status:** Accepted

**Date:** 2026-07-07

**Authors:** SafetyMAIN Architecture Team

---

# Context

SafetyMAIN is designed as a long-term enterprise platform for managing occupational safety, industrial safety, explosives safety, compliance, documentation, knowledge and AI services.

Traditional enterprise systems are usually document-centric or table-centric.

As the platform evolves, the number of entity types, document types and relationships will continuously grow.

Using isolated database tables and independent business objects would significantly increase system complexity.

A more universal architectural model is required.

---

# Decision

SafetyMAIN adopts an **Entity-Centric Architecture**.

Every business object inside the platform is an Entity.

Examples include:

- Organization
- Department
- Employee
- Profession
- Equipment
- Hazard
- Risk
- PPE
- OPO
- Document
- Template
- Regulation
- Industrial Safety Expertise
- Blasting Permit
- License
- Training Program
- Presentation
- Video
- Quiz
- AI Agent
- Task

Each entity inherits the same core capabilities from the platform.

Entity behavior is extended through metadata, relations and modules rather than custom implementations.

---

# Core Principles

Every Entity shall support:

- Globally unique identifier (UUID)
- Versioning
- Audit history
- Metadata
- Extensions
- Attachments
- Relationships
- Tags
- Comments
- Tasks
- AI Summary
- Embeddings
- Search indexing
- Permissions
- Organization ownership

---

# Benefits

The Entity-Centric Architecture provides:

- Consistent domain model
- Reduced code duplication
- Simpler API design
- Unified search
- Native AI integration
- Flexible metadata model
- Easier module development
- Long-term maintainability

---

# Consequences

All future platform modules must be implemented using the Entity model.

Creating isolated business objects outside the Entity model is prohibited unless explicitly approved through a future ADR.

Every new module shall integrate with:

- Metadata Engine
- Knowledge Graph
- Versioning
- Audit
- AI Services
- Permissions

---

# Alternatives Considered

## Traditional relational model

Rejected.

Reason:

Large number of duplicated implementations.

---

## Document-centric architecture

Rejected.

Reason:

Documents are outputs generated from knowledge rather than primary business objects.

---

## Microservice-specific domain models

Rejected.

Reason:

Would reduce interoperability between platform modules.

---

# Related ADRs

- ADR-0002 Metadata-Driven Platform (planned)
- ADR-0003 Knowledge Graph (planned)
- ADR-0004 Version Everything (planned)

---

# Decision Summary

SafetyMAIN is fundamentally an Entity-Centric Platform.

Everything inside the platform is represented as an Entity with shared capabilities.

Documents are considered generated representations of knowledge rather than the primary source of truth.
