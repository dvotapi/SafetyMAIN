# Architecture Decision Freeze

Version: 1.0

Status: Approved

Date: 2026-07-07

---

# Purpose

This document establishes the architectural decisions that are considered stable for the SafetyMAIN platform.

The purpose of the freeze is to protect the core architecture from uncontrolled changes during implementation.

Future modifications require an Architecture Decision Record (ADR) and an Architecture Review.

---

# Frozen Decisions

## 1. Knowledge Object First

Knowledge Objects are the universal representation of enterprise knowledge.

All business concepts are represented as Knowledge Objects.

No module may introduce an alternative business object model.

---

## 2. Documents Are Generated Artifacts

Documents are not the source of truth.

Knowledge is the source of truth.

All documents are generated from Knowledge Objects.

---

## 3. Metadata Driven Platform

Platform behavior is described by metadata whenever possible.

Business customization shall be performed through metadata instead of source code.

---

## 4. Compliance Rules Engine

Business behavior belongs to Compliance Rules.

Application code shall implement the platform.

Compliance Rules shall implement enterprise behavior.

---

## 5. Obligations Engine

The platform manages enterprise obligations rather than documents.

Obligations are first-class Knowledge Objects.

---

## 6. Hybrid Storage Model

The primary storage architecture consists of:

- PostgreSQL
- JSONB
- pgvector
- MinIO
- Redis

Graph capabilities are implemented logically through Knowledge Object Relations.

---

## 7. Multi-Tenant by Design

Every Knowledge Object belongs to an Organization.

Organization is the primary security and ownership boundary.

---

## 8. AI Native

Artificial Intelligence is a native platform capability.

AI participates in:

- Search
- Classification
- Recommendations
- Document Generation
- Presentation Generation
- Video Generation
- Compliance Analysis

---

## 9. Explainable AI

Every AI recommendation shall reference its supporting Knowledge Objects, Rules and Regulations whenever possible.

---

## 10. Version Everything

The platform versions:

- Knowledge Objects
- Metadata
- Rules
- Obligations
- Documents
- Templates
- Prompts
- AI Models
- Configurations

---

## 11. Architecture Before Implementation

Implementation begins only after architecture and specifications are approved.

---

## 12. One Concept — One Term

Official terminology is maintained in the Domain Dictionary.

No duplicate business terminology is allowed.

---

## 13. Code Describes the Platform

Platform behavior belongs in source code.

---

## 14. Metadata Describes the Business

Business variability belongs in metadata.

---

## 15. Rules Describe the Behavior

Business workflows are described through Compliance Rules.

---

# Change Policy

Frozen decisions shall not be modified directly.

Changes require:

1. New ADR
2. Architecture Review
3. Impact Analysis
4. Approval

---

# Summary

These principles define the immutable architectural foundation of SafetyMAIN Core.

All future modules, services and components shall comply with this document.
