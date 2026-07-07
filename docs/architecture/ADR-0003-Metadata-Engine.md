# ADR-0003 — Metadata Engine

**Status:** Accepted

**Date:** 2026-07-07

**Authors:** SafetyMAIN Architecture Team

---

# Context

SafetyMAIN is designed as a long-term extensible platform.

The number of Knowledge Objects, fields, modules and generated artifacts will continuously grow.

Changing the application source code every time a new field or property is introduced is not acceptable.

A metadata-driven architecture is required.

---

# Decision

SafetyMAIN adopts a universal Metadata Engine.

Metadata defines the structure and behavior of every Knowledge Object.

Business objects shall not contain hardcoded field definitions whenever metadata can describe them.

---

# Metadata Responsibilities

The Metadata Engine defines:

- field definitions
- data types
- validation rules
- required fields
- default values
- visibility
- editability
- permissions
- search indexing
- AI participation
- document generation
- localization
- UI rendering

---

# Metadata Capabilities

Metadata shall support:

- custom fields
- dynamic forms
- field groups
- calculated fields
- enumerations
- dictionaries
- references
- file fields
- collections
- nested objects

---

# Principles

- Metadata over code
- Configuration before implementation
- Extensibility by design
- Backward compatibility
- AI-aware metadata
- Generated UI
- Generated API where applicable

---

# Benefits

- No code changes for new fields
- Faster customization
- Easier customer-specific configuration
- Unified user experience
- Lower maintenance cost
- Future-proof architecture

---

# Consequences

Every future module shall use the Metadata Engine.

Direct hardcoding of business fields should be avoided unless technically justified.

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0002 Knowledge Object Specification
- ADR-0004 Rules Engine (planned)
- ADR-0005 Knowledge Graph (planned)

---

# Decision Summary

Metadata becomes the primary mechanism for describing Knowledge Objects and their behavior.

Platform evolution should be achieved through metadata before code changes are considered.
