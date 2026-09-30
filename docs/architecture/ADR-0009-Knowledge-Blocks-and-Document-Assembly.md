# ADR-0009 — Knowledge Blocks and Document Assembly

**Status:** Accepted

**Date:** 2026-09-14

**Authors:** SafetyMAIN Architecture Team

---

# Context

The organization keeps its safety instructions and other local normative acts as PDF files.

Instructions repeat large parts of each other: general requirements, personal protective equipment, emergency actions. Every new instruction is typed from scratch, and the link between a sentence and the regulation behind it is lost.

The architecture already states:

- Knowledge is the source of truth; documents are generated artifacts (ADR-0001; Architecture Decision Freeze §2).
- AI is native and assists, but does not replace human responsibility (Architecture Constitution, Article VI; Freeze §8).
- AI recommendations reference their supporting knowledge whenever possible (Freeze §9 Explainable AI).
- Documents, templates, prompts, and AI models are versioned (Freeze §10 Version Everything).
- pgvector is part of the Hybrid Storage Model (Freeze §6).

Current state:

- `backend/core/infrastructure/ai/` is an empty package; `pyproject.toml` has no LLM or embedding client dependency;
- pgvector is not installed;
- `DocumentType` and `ComplianceDocument` are introduced by P11-001.

Epic P11 has already decided:

- chat models are used through the OpenCode Zen gateway (OpenAI-compatible);
- embeddings are produced by Z.ai directly;
- vector search uses pgvector in the existing PostgreSQL;
- free-tier models are forbidden for internal documents.

---

# Decision

An instruction is an **assembly of reusable Knowledge Blocks**, not a monolithic text.

Three concepts carry the model:

- `KnowledgeBlock` — a reusable fragment of normative content;
- `DocumentTemplate` — the mandatory structure of a document type;
- `DocumentAssembly` — a template filled with block versions for a concrete case.

Generating an assembly produces a version of a `ComplianceDocument`.

Existing PDF documents are decomposed into Knowledge Blocks. New documents are assembled from them.

Knowledge Blocks, Document Templates, and Document Assemblies belong to an organization. Candidate selection, semantic search, and deduplication consider only objects of the caller's organization; objects of another organization are reported as not found (404).

---

# Knowledge Block

`KnowledgeBlock` is a Knowledge Object (ADR-0002).

| Attribute | Meaning |
|---|---|
| Text | Block content in Markdown |
| Section kind | The part of a document the block belongs to, for example "before work" |
| Safety domain | One of the safety domains of the platform |
| Provenance | Source document and page, or regulation and clause |
| Version | Block version |
| Curation status | Where the block stands in curation |
| Applicability tags | Asset type, role or position, process or work type, hazard factor, regulation |

- Editing a block creates a new block version. Previous versions stay readable.
- Provenance makes a block explainable (Freeze §9): a curator and a reader can trace the text to its source. A block without a source document or regulation, for example one drafted by AI or written by an author, is marked as such.
- Enumerations, curation statuses, and persistence are specified by P11-002.

---

# Document Template

`DocumentTemplate` defines the mandatory structure per document type.

For an instruction the sections are:

1. General requirements
2. Before work
3. During work
4. Emergencies
5. After work
6. Responsibility

- Templates are data described by metadata (ADR-0003), not code. Adding a section requires no code change.
- Templates are versioned (Freeze §10).

---

# Document Assembly

```text
DocumentAssembly = template + ordered list of block versions + parameters + author edits
```

- An assembly references **block versions**, not blocks. A later change of a block never silently changes an assembled document.
- Parameters describe the concrete case: asset, role or position, processes, and hazard factors.
- Author edits are kept in the assembly, separately from the blocks. An edit never changes a shared block.
- Generating an assembly produces a `ComplianceDocument` version. Regenerating produces a new version; previous versions stay.
- Because assemblies keep block-version references, a change of a block finds every document assembled from an earlier version of it.
- A block change never regenerates documents automatically. Finding affected documents supports their review through the Obligations Engine (ADR-0005).

Document generation runs in the background worker (ADR-0007) and stores its files in object storage (ADR-0006).

---

# Human in the Loop

Every step that uses AI is Human in the Loop.

AI proposes:

- document classification;
- segmentation into blocks;
- tagging;
- deduplication;
- drafted blocks for gaps in an assembly.

Rules:

- Every AI result is `draft` until a curator confirms it.
- Only confirmed blocks enter assemblies.
- AI results stay visibly marked until confirmation.
- Confirmation is a user action and is audited.

---

# AI Ports and Adapters

| Port | Capability | Adapter | Used with |
|---|---|---|---|
| `AIProviderContract` | Chat completion, structured output | `OpenAICompatibleChatProvider` | OpenCode Zen |
| `EmbeddingProviderContract` | Text embeddings | `OpenAICompatibleEmbeddingProvider` | Z.ai |

- Ports live in `backend/core/contracts/`.
- Adapters live in `backend/core/infrastructure/ai/`.
- Base URL, API key, and model name of each adapter are settings.
- Structured output is validated against the expected schema before it is used.
- Domain and application layers never import HTTP clients or vendor SDKs.

Specific model names are not decided here; they are settings chosen per task in P11-002.

---

# Embeddings

- Embeddings are stored with pgvector in the existing PostgreSQL.
- The embedding model name and the embedding dimension are settings.
- The dimension is frozen in the pgvector migration.
- The dimension setting must match the migration. A mismatch is a startup error.
- Changing the embedding model requires re-embedding all blocks. Similarity is computed only between vectors produced by the same model.

---

# Prompts and AI Call Log

- Prompt templates are versioned files in the repository (Freeze §10). A changed prompt is a new prompt version.
- Every AI call is logged with prompt version, model, token usage, and the id of the produced object.
- An object produced by AI can therefore be traced to the prompt version and the model that produced it (Freeze §9).
- The log never contains API keys.
- Document text is never written to audit metadata. Whether request and response payloads are stored is decided by P11-002.

---

# Model Policy

- Free-tier gateway models are not allowed for internal documents.
- Model choice follows the task: cheaper models for segmentation, stronger models for classification and drafting (epic P11 decision).

---

# Principles

- Knowledge lives in blocks; documents are assembled evidence.
- Reuse blocks instead of rewriting text.
- AI proposes; people confirm.
- Every block is traceable to its source; every AI result is traceable to its prompt and model.
- Blocks, templates, and prompts are versioned.
- AI providers stay behind ports.

---

# Consequences

- P11-002 introduces the AI ports and adapters, AI settings, the AI call log, prompt files, the pgvector migration, `KnowledgeBlock`, and the curation workflow.
- P11-002 extends the architecture tests so that domain and application layers cannot import HTTP clients or LLM SDKs.
- P11-003 introduces `DocumentTemplate`, `DocumentAssembly`, and generation into `ComplianceDocument`. The internal regulation on electronic document flow required by ADR-0010 can be produced this way.
- The pgvector extension must be enabled on the production database server. `docs/infrastructure/ApplicationServerDeployment.md` is updated by P11-002.
- Changing the embedding model requires re-embedding all blocks; a model with another dimension also requires a new migration.
- Internal document text is sent to external chat and embedding providers. This follows the epic P11 provider decision; the free-tier prohibition limits that exposure.
- AI cost and availability become external dependencies. AI failures surface as failed worker jobs and never break API requests (ADR-0007).

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0002 Knowledge Object Specification
- ADR-0003 Metadata Engine
- ADR-0005 Obligations Engine
- ADR-0006 Document and Evidence Storage
- ADR-0007 Background Worker and Scheduling
- ADR-0010 Electronic Journals and Simple Electronic Signature

---

# Decision Summary

Instructions are assembled from reusable, versioned, tagged Knowledge Blocks according to a Document Template.

An assembly references block versions, so every affected document is found when a block changes.

AI proposes classification, segmentation, tags, deduplication, and drafts; only curator-confirmed blocks enter assemblies.

AI providers stay behind `AIProviderContract` and `EmbeddingProviderContract`; prompts are versioned and every AI call is logged.
