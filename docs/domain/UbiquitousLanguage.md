# Safety Domain Ubiquitous Language

Status: Active  
Date: 2026-07-24  
Task: TASK-P8-001

Related documents:

- [SafetyDomainFoundation.md](SafetyDomainFoundation.md)
- [Aggregates.md](Aggregates.md)
- [DomainEvents.md](DomainEvents.md)
- [LifecycleRules.md](LifecycleRules.md)
- [DomainDictionary.md](DomainDictionary.md) — platform-wide dictionary; Safety terms below are authoritative for OHS concepts
- [ArchitectureConstitution.md](../architecture/ArchitectureConstitution.md) — Article X (One Concept → One Term)

---

## 1. Purpose

This glossary defines the Occupational Health and Safety (OHS) ubiquitous language for
SafetyMAIN. Application code, APIs, audit metadata, and future UI copy must use these
terms consistently.

Knowledge Objects remain the platform’s general knowledge substrate. Safety aggregates
are **business operational records** that may *reference* Knowledge Objects; they are not
generic Knowledge Objects themselves.

---

## 2. Core Terms

### Hazard

| Field | Content |
|-------|---------|
| **Definition** | A source, situation, or act with potential to cause harm to people, property, or the environment. |
| **Business meaning** | The starting point of proactive risk management: identify what can go wrong before work proceeds. |
| **Aliases** | None preferred. Avoid “danger” in formal records. |
| **Relationships** | Assessed through one or more `Risk` records; may relate to `Asset`, `Location` / `Work Area`, `Chemical`. |
| **Examples** | Unguarded rotating machinery; wet floor in a corridor; chlorine gas cylinder storage. |
| **Non-examples** | A completed injury report (`Incident`); a numeric score (`RiskLevel`); a training course. |

### Risk

| Field | Content |
|-------|---------|
| **Definition** | The combination of the likelihood of a hazardous event and the severity of its consequences. |
| **Business meaning** | Quantifies or classifies exposure so the organization can prioritize controls. |
| **Aliases** | May appear as “risk rating” colloquially; formal records use `Risk` / `Risk Assessment`. |
| **Relationships** | Always about a `Hazard`; reduced by `Control`s; produces inherent and residual views. |
| **Examples** | Medium likelihood / high severity for forklift–pedestrian interaction. |
| **Non-examples** | The hazard itself; a control measure; an inspection checklist. |

### Risk Assessment

| Field | Content |
|-------|---------|
| **Definition** | The structured process and recorded outcome of evaluating risks arising from hazards. |
| **Business meaning** | The governed decision artifact: who assessed, when, method, ratings, and acceptance. |
| **Aliases** | “RA”; “JSA/JHA” may feed into a Risk Assessment but are not synonyms unless policy equates them. |
| **Relationships** | Owns or produces `Risk` evaluations; triggers `Control` selection; may require reassessment. |
| **Examples** | Task-based assessment for confined-space entry; annual plant risk register update. |
| **Non-examples** | Ad-hoc verbal warning; incident investigation root cause (related but distinct). |

### Control

| Field | Content |
|-------|---------|
| **Definition** | A measure that eliminates a hazard or reduces risk. |
| **Business meaning** | The actionable response placed on the Hierarchy of Controls. |
| **Aliases** | “Control measure”; “safeguard”. |
| **Relationships** | Attached to a `Risk`; verified by `Inspection` / `Evidence`; may generate `Corrective Action`. |
| **Examples** | Machine guard; substitution of solvent; mandatory lockout procedure; safety glasses. |
| **Non-examples** | The hazard description alone; a risk score without a measure. |

### Hierarchy of Controls

| Field | Content |
|-------|---------|
| **Definition** | Ordered preference for selecting controls: Elimination → Substitution → Engineering → Administrative → PPE. |
| **Business meaning** | Prefer more effective/reliable controls over reliance on human behavior or PPE alone. |
| **Aliases** | “HoC”; “control hierarchy”. |
| **Relationships** | Classifies each `Control`; informs future rule-engine recommendations. |
| **Examples** | Eliminating a toxic process step before requiring respirators. |
| **Non-examples** | A free-form priority list unrelated to effectiveness of risk reduction. |

### Inspection

| Field | Content |
|-------|---------|
| **Definition** | A planned or triggered examination of a workplace, asset, or process against criteria. |
| **Business meaning** | Detects deviations early and produces Findings that drive action. |
| **Aliases** | “Check”; “audit” is **not** an alias (see Audit). |
| **Relationships** | May cover `Asset` / `Location`; produces `Finding`s; may verify `Control`s. |
| **Examples** | Weekly fire-extinguisher check; pre-use vehicle inspection. |
| **Non-examples** | Regulatory compliance audit program; emergency response drill. |

### Finding

| Field | Content |
|-------|---------|
| **Definition** | A recorded deviation, deficiency, or observation outcome discovered during an Inspection (or similar verification). |
| **Business meaning** | The actionable gap between expected and actual condition. |
| **Aliases** | “Non-conformance” when policy uses NCR language; prefer Finding in SafetyMAIN. |
| **Relationships** | Owned by `Inspection`; may spawn `Corrective Action` / `Preventive Action`. |
| **Examples** | Missing machine guard; expired first-aid kit. |
| **Non-examples** | The inspection plan itself; an incident report. |

### Observation

| Field | Content |
|-------|---------|
| **Definition** | A recorded note of a condition or behavior that may be positive, neutral, or concerning, without necessarily asserting a formal Finding. |
| **Business meaning** | Captures leading indicators and culture signals. |
| **Aliases** | “Safety observation”; “BBS observation”. |
| **Relationships** | May escalate to `Finding` or feed `Hazard` identification. |
| **Examples** | Worker correctly using harness; near-miss verbal report not yet classified. |
| **Non-examples** | Formally closed Corrective Action; signed Permit To Work. |

### Incident

| Field | Content |
|-------|---------|
| **Definition** | An unplanned event that resulted in, or could have resulted in, injury, illness, damage, or environmental harm. |
| **Business meaning** | Triggers response, investigation, learning, and corrective/preventive action. |
| **Aliases** | “Event” (too vague — avoid as primary term). |
| **Relationships** | May include `Near Miss`; leads to investigation, root cause, `Corrective Action`. |
| **Examples** | Slip resulting in sprain; chemical splash with no injury after PPE held. |
| **Non-examples** | Planned emergency drill; routine inspection finding. |

### Near Miss

| Field | Content |
|-------|---------|
| **Definition** | An Incident in which harm did not occur but was narrowly avoided. |
| **Business meaning** | High-value leading indicator; treated with investigation seriousness proportionate to potential. |
| **Aliases** | “Close call”; “near hit”. |
| **Relationships** | Subtype or classification of `Incident`. |
| **Examples** | Tool dropped from height into empty exclusion zone. |
| **Non-examples** | Actual injury; hypothetical risk in a Risk Assessment. |

### Corrective Action

| Field | Content |
|-------|---------|
| **Definition** | An action taken to eliminate the cause of a detected nonconformity or other undesirable situation. |
| **Business meaning** | Fixes the underlying problem so recurrence is reduced. |
| **Aliases** | “CA”; “CAPA” when combined with Preventive Action in one record (document carefully). |
| **Relationships** | May originate from `Finding`, `Incident`, audit, or risk review; has assignee and verification. |
| **Examples** | Redesign guard after repeated Finding; retrain after procedure breach. |
| **Non-examples** | Immediate first aid (response, not corrective root-cause action). |

### Preventive Action

| Field | Content |
|-------|---------|
| **Definition** | An action taken to eliminate the cause of a *potential* nonconformity or other undesirable potential situation. |
| **Business meaning** | Proactive improvement before failure occurs. |
| **Aliases** | “PA”; often paired with Corrective Action. |
| **Relationships** | May arise from Risk Assessment, trend analysis, or Near Miss learning. |
| **Examples** | Install barriers after near-miss trend in a corridor. |
| **Non-examples** | Closing an inspection without addressing causes. |

### Training

| Field | Content |
|-------|---------|
| **Definition** | Structured learning provided to develop knowledge or skill required for safe work. |
| **Business meaning** | Builds and evidences competency prerequisites for roles and permits. |
| **Aliases** | “Course”; “instruction” (prefer Training for formal records). |
| **Relationships** | Produces or supports `Competency`; may be required by `Permit To Work` or `Control`. |
| **Examples** | Confined-space entry course; annual fire warden refresher. |
| **Non-examples** | A toolbox talk without assessment (may be Administrative Control, not full Training record). |

### Competency

| Field | Content |
|-------|---------|
| **Definition** | Demonstrated ability to apply knowledge and skills to perform work safely and correctly. |
| **Business meaning** | Authorization basis beyond attendance: person is fit for the task. |
| **Aliases** | “Qualification”; “authorization” (authorization may be broader). |
| **Relationships** | Evidence from `Training`, assessment, experience; gates `Permit` roles. |
| **Examples** | Certified forklift operator current within validity period. |
| **Non-examples** | Job title alone; incomplete e-learning progress. |

### Permit To Work

| Field | Content |
|-------|---------|
| **Definition** | A formal documented authorization that specified work may proceed under defined precautions. |
| **Business meaning** | High-risk work control: isolations, gas tests, PPE, validity window, issuer/acceptor. |
| **Aliases** | “PTW”; “work permit”. |
| **Relationships** | References `Location` / `Asset`, `Hazard`s, required `Competency`, `PPE`. |
| **Examples** | Hot work permit; confined space entry permit. |
| **Non-examples** | General site induction badge; informal verbal approval. |

### Asset

| Field | Content |
|-------|---------|
| **Definition** | A tangible item of value managed by the organization for operations (plant, vehicle, tool, structure). |
| **Business meaning** | Anchor for inspections, hazards, maintenance, and permits. |
| **Aliases** | “Plant item”; prefer Asset in SafetyMAIN. |
| **Relationships** | Located in `Location` / `Work Area`; subject of `Inspection`; may be `Equipment`. |
| **Examples** | Air compressor unit #AC-12; company light vehicle. |
| **Non-examples** | A software license; a person. |

### Equipment

| Field | Content |
|-------|---------|
| **Definition** | An Asset (or Asset subtype) used to perform work or provide a process function. |
| **Business meaning** | Emphasizes operational use and safeguarding. |
| **Aliases** | Often used interchangeably with Asset; prefer Asset as aggregate root, Equipment as classification. |
| **Relationships** | Same as Asset; may have `PPE` interfaces or guarding `Control`s. |
| **Examples** | Angle grinder; HVAC exhaust fan. |
| **Non-examples** | A building floor plate (Location); a chemical substance. |

### Location

| Field | Content |
|-------|---------|
| **Definition** | A physical place in the organization’s estate (site, building, floor, outdoor area). |
| **Business meaning** | Spatial context for work, emergencies, and inspections. |
| **Aliases** | “Site”; “facility” (facility may be a Location hierarchy node). |
| **Relationships** | Contains `Work Area`s; hosts `Asset`s; scoped for `Emergency Plan`. |
| **Examples** | Warehouse B; Roof level 3. |
| **Non-examples** | A postal address without operational meaning; a logical org unit. |

### Work Area

| Field | Content |
|-------|---------|
| **Definition** | A defined subspace of a Location where a specific activity or team operates. |
| **Business meaning** | Finer zoning for hazards, permits, and emergency assembly. |
| **Aliases** | “Zone”; “bay”. |
| **Relationships** | Child of `Location`; may have local `Hazard`s and `PPE` rules. |
| **Examples** | Paint booth; loading dock lane 2. |
| **Non-examples** | An entire multi-site company. |

### Contractor

| Field | Content |
|-------|---------|
| **Definition** | An external party engaged to perform work for the organization. |
| **Business meaning** | Distinct from Employee for induction, permit, and liability workflows. |
| **Aliases** | “Vendor”; “supplier” (supplier may be broader). |
| **Relationships** | May hold `Competency` evidence; appears on `Permit To Work`; subject to site rules. |
| **Examples** | Scaffolding firm crew; electrical contractor. |
| **Non-examples** | Permanent employee; visitor on a tour. |

### Employee

| Field | Content |
|-------|---------|
| **Definition** | A person employed by the organization (or defined employment relationship under local policy). |
| **Business meaning** | Primary workforce identity for training, competency, and incident involvement. |
| **Aliases** | “Worker” (broader — includes contractors in some jurisdictions). |
| **Relationships** | Links to platform `User` when accounts exist; holds `Competency`. |
| **Examples** | Production operator; HSE advisor. |
| **Non-examples** | Anonymous public visitor; equipment. |

### Visitor

| Field | Content |
|-------|---------|
| **Definition** | A person temporarily on site who is neither Employee nor Contractor performing work. |
| **Business meaning** | Requires escort/induction controls without full worker competency profiles. |
| **Aliases** | “Guest”. |
| **Relationships** | May be recorded for emergency headcount; limited `Permit` involvement. |
| **Examples** | Client auditor tour; family open day. |
| **Non-examples** | Contractor welding on plant. |

### Chemical

| Field | Content |
|-------|---------|
| **Definition** | A substance or mixture used, stored, or generated that may present health, physical, or environmental hazards. |
| **Business meaning** | Drives SDS, labeling, storage, and exposure controls. |
| **Aliases** | “Substance”; “hazardous material” / “HazMat”. |
| **Relationships** | Has `SDS`; may create `Hazard`s; informs `PPE` and `Emergency` response. |
| **Examples** | Acetone drum; welding fume (process-generated). |
| **Non-examples** | A machine; a training module. |

### SDS

| Field | Content |
|-------|---------|
| **Definition** | Safety Data Sheet — standardized information on a Chemical’s hazards and safe handling. |
| **Business meaning** | Authoritative reference for storage, PPE, first aid, and spill response. |
| **Aliases** | “MSDS” (legacy). |
| **Relationships** | Belongs to a `Chemical`; referenced by Risk Assessments and Emergency Plans. |
| **Examples** | Manufacturer SDS revision 5 for sulfuric acid. |
| **Non-examples** | A workplace risk assessment; a label alone. |

### PPE

| Field | Content |
|-------|---------|
| **Definition** | Personal Protective Equipment — equipment worn to minimize exposure to hazards. |
| **Business meaning** | Lowest preferred Hierarchy of Controls tier; still mandatory when required. |
| **Aliases** | “Personal protective clothing” subset. |
| **Relationships** | `Control` of type PPE; required by `Permit`, task, or area rules. |
| **Examples** | Safety helmet; chemical splash goggles. |
| **Non-examples** | Fixed machine guard (Engineering Control); procedure (Administrative). |

### Emergency

| Field | Content |
|-------|---------|
| **Definition** | A serious unexpected situation requiring immediate response to protect people, assets, or environment. |
| **Business meaning** | Activates plans, roles, and communications outside normal operations. |
| **Aliases** | Avoid using interchangeably with `Incident` (incident may or may not be an emergency). |
| **Relationships** | Governed by `Emergency Plan`; practiced via `Emergency Drill`. |
| **Examples** | Fire alarm activation; major chemical release. |
| **Non-examples** | Minor first-aid cut with no evacuation. |

### Emergency Plan

| Field | Content |
|-------|---------|
| **Definition** | Documented arrangements for responding to defined emergency scenarios. |
| **Business meaning** | Roles, routes, contacts, equipment, and escalation paths. |
| **Aliases** | “ERP”; “emergency response plan”. |
| **Relationships** | Scoped to `Location`s; references `Chemical`/SDS; validated by drills. |
| **Examples** | Site fire and evacuation plan; spill response plan. |
| **Non-examples** | A single incident report. |

### Emergency Drill

| Field | Content |
|-------|---------|
| **Definition** | A practiced exercise of an Emergency Plan (full or partial). |
| **Business meaning** | Verifies readiness and produces findings for improvement. |
| **Aliases** | “Evacuation drill”; “tabletop exercise” (subtype). |
| **Relationships** | References `Emergency Plan`; may create `Finding`s / `Corrective Action`s. |
| **Examples** | Annual site evacuation; spill tabletop. |
| **Non-examples** | Real emergency response (operational Emergency, not a drill). |

### Audit

| Field | Content |
|-------|---------|
| **Definition** | A systematic, independent, and documented process for obtaining evidence and evaluating it objectively. |
| **Business meaning** | Assurance of management system effectiveness — broader and more formal than Inspection. |
| **Aliases** | Do not alias to Inspection. |
| **Relationships** | Evaluates against `Compliance Requirement`s; produces findings and actions. |
| **Examples** | Internal ISO 45001 audit; contractor HSE audit. |
| **Non-examples** | Daily forklift pre-use check (`Inspection`). |

### Compliance Requirement

| Field | Content |
|-------|---------|
| **Definition** | An obligation arising from law, regulation, standard, permit condition, or internal policy. |
| **Business meaning** | External (or policy) “must” that Safety controls and evidence must satisfy. |
| **Aliases** | “Obligation”; “requirement”. |
| **Relationships** | Provided by Knowledge / Compliance modules; mapped to `Control`s and `Evidence`. |
| **Examples** | “Provide SDS for hazardous chemicals on site”; LOTO regulatory duty. |
| **Non-examples** | A Control measure; a completed Evidence file alone. |

### Evidence

| Field | Content |
|-------|---------|
| **Definition** | Recorded proof that a requirement, control, or action has been fulfilled. |
| **Business meaning** | Supports verification and auditability (Constitution: documents are evidence, not the source of truth). |
| **Aliases** | “Record”; “artifact”. |
| **Relationships** | Attached to Controls, Training completion, Permit close-out, Corrective Action verification. |
| **Examples** | Signed permit form; training certificate; photo of installed guard. |
| **Non-examples** | An unverified verbal claim; the requirement text itself. |

---

## 3. Naming Rules

1. Prefer the **Name** column term in code identifiers (`Hazard`, `PermitToWork`, not `Danger`, `WorkPass`).
2. Status enums use the lifecycle names in [LifecycleRules.md](LifecycleRules.md).
3. Platform identity terms (`User`, `Organization`, `Membership`) remain as defined in identity docs; Safety “Employee” may link to `User` but is a distinct business concept.
4. Knowledge Object types may *mirror* these terms for knowledge graphs; operational Safety aggregates remain separate transactional records.
