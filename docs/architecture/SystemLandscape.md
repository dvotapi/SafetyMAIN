# TASK-0007

## Title

Create SafetyMAIN System Landscape

---

## Goal

Describe the complete high-level architecture of the SafetyMAIN platform.

This document shall become the primary navigation map for the entire system.

It must describe the platform from a system perspective rather than implementation details.

---

## Create

docs/architecture/SystemLandscape.md

---

## Sections

# Vision

Describe SafetyMAIN as an Enterprise Compliance Operating System (ECOS).

---

# Core Platform

Describe the platform core.

Include:

Knowledge Objects

Metadata Engine

Compliance Rules Engine

Obligations Engine

Knowledge Graph

AI Services

Generated Artifacts

---

# Business Modules

Describe future modules.

Occupational Safety

Industrial Safety

Explosives Safety

Fire Safety

Road Safety

Environmental Safety

Training

Document Generation

Risk Management

Incident Management

Audit Management

Contractor Management

Equipment Management

Medical Examinations

PPE

Emergency Response

---

# Infrastructure

Describe:

Frontend

Backend API

Workers

AI Services

Object Storage

PostgreSQL

Redis

Search

Monitoring

Logging

Authentication

---

# External Systems

Describe possible integrations.

ERP

HR

Active Directory

Email

Telegram

WhatsApp

Microsoft Teams

GIS

SCADA

IoT

Document Management Systems

Government Services

---

# AI Layer

Describe:

LLMs

RAG

OCR

Speech-to-Text

Text-to-Speech

Presentation Generator

Video Generator

Knowledge Search

Compliance Assistant

---

# Future Platform

Describe long-term evolution.

---

## Acceptance Criteria

✓ Complete system overview

✓ No implementation details

✓ Consistent with all ADRs

✓ Ready for C4 diagrams

---

# Infrastructure Decision Status (P11)

- Workers — decided, see [ADR-0007](ADR-0007-Background-Worker-and-Scheduling.md)
- Object Storage — decided, see [ADR-0006](ADR-0006-Document-and-Evidence-Storage.md)
- AI Services — decided, see [ADR-0009](ADR-0009-Knowledge-Blocks-and-Document-Assembly.md)
- Redis — not required for the P11 scope, see [ADR-0007](ADR-0007-Background-Worker-and-Scheduling.md); Redis stays in [Architecture Decision Freeze](ArchitectureDecisionFreeze.md) §6
