import type {
  EvidenceDto,
  ImplementationDto,
  MilestoneDto,
  OwnerDto,
  ReviewScheduleDto,
  RiskControlDto,
  RiskControlListDto,
  SourceDto,
  VerificationDto,
  WrappedIdDto,
} from "@/features/risk-controls/types/risk-control-dto";
import type {
  RiskControl,
  RiskControlEvidence,
  RiskControlImplementation,
  RiskControlListResult,
  RiskControlMilestone,
  RiskControlOwner,
  RiskControlReviewSchedule,
  RiskControlSource,
  RiskControlVerification,
} from "@/features/risk-controls/types/risk-control-types";

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function readNullableString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function readNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

/** Backend wraps some ids as {"value": uuid} and leaves others flat. */
export function readWrappedId(value: WrappedIdDto | undefined): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string") {
    return value;
  }
  const inner = asRecord(value)["value"];
  return typeof inner === "string" ? inner : null;
}

export function mapOwnerDto(dto: OwnerDto | null): RiskControlOwner | null {
  if (!dto) {
    return null;
  }
  const snapshot = readString(dto.display_name_snapshot).trim();
  const reference = readString(dto.owner_reference).trim();
  return {
    ownerType: readString(dto.owner_type, "user"),
    ownerReference: reference,
    displayNameSnapshot: snapshot,
    assignedAt: readNullableString(dto.assigned_at),
    assignedBy: readNullableString(dto.assigned_by),
    label: snapshot || reference,
  };
}

function mapMilestone(value: MilestoneDto | unknown): RiskControlMilestone {
  const record = asRecord(value);
  return {
    id: readNullableString(record["id"]),
    title: readString(record["title"]),
    description: readString(record["description"]),
    dueDate: readNullableString(record["due_date"]),
    status: readString(record["status"], "pending"),
    completedAt: readNullableString(record["completed_at"]),
    evidenceRefs: readStringArray(record["evidence_refs"]),
  };
}

export function mapImplementationDto(
  value: ImplementationDto | Record<string, unknown> | null | undefined,
): RiskControlImplementation {
  const record = asRecord(value);
  const milestones = Array.isArray(record["milestones"])
    ? (record["milestones"] as unknown[]).map(mapMilestone)
    : [];
  return {
    targetStartDate: readNullableString(record["target_start_date"]),
    targetCompletionDate: readNullableString(record["target_completion_date"]),
    actualStartDate: readNullableString(record["actual_start_date"]),
    actualCompletionDate: readNullableString(record["actual_completion_date"]),
    implementationMethod: readString(record["implementation_method"]),
    milestones,
    dependencies: readStringArray(record["dependencies"]),
    resourceNotes: readString(record["resource_notes"]),
    evidenceRequirements: readStringArray(record["evidence_requirements"]),
    progress: readNumber(record["progress"], 0),
    summary: readString(record["summary"]),
    evidenceWaiverReason: readNullableString(record["evidence_waiver_reason"]),
  };
}

function mapEvidence(dto: EvidenceDto): RiskControlEvidence {
  return {
    id: dto.id,
    evidenceType: readString(dto.evidence_type, "other"),
    externalReference: readString(dto.external_reference),
    title: readString(dto.title),
    description: readString(dto.description),
    capturedAt: readNullableString(dto.captured_at),
    capturedByUserId: readWrappedId(dto.captured_by),
    checksum: readNullableString(dto.checksum),
    metadata: asRecord(dto.metadata) as Record<string, string>,
  };
}

function mapVerification(dto: VerificationDto): RiskControlVerification {
  return {
    id: dto.id,
    verificationType: readString(dto.verification_type, "other"),
    method: readString(dto.method),
    criteria: readString(dto.criteria),
    performedAt: readNullableString(dto.performed_at),
    performedByUserId: readWrappedId(dto.performed_by),
    result: readString(dto.result),
    rating: readNullableString(dto.rating),
    findings: readString(dto.findings),
    evidenceRefs: readStringArray(dto.evidence_refs),
    nextAction: readNullableString(dto.next_action),
    nextReviewDate: readNullableString(dto.next_review_date),
    profileKey: readString(dto.profile_key, "default"),
    profileVersion: readString(dto.profile_version, "1"),
  };
}

export function mapReviewScheduleDto(
  value: ReviewScheduleDto | Record<string, unknown> | null | undefined,
): RiskControlReviewSchedule {
  const record = asRecord(value);
  const required = record["review_required"];
  return {
    reviewRequired: typeof required === "boolean" ? required : true,
    reviewFrequencyDays:
      typeof record["review_frequency_days"] === "number"
        ? (record["review_frequency_days"] as number)
        : null,
    nextReviewDate: readNullableString(record["next_review_date"]),
    lastReviewDate: readNullableString(record["last_review_date"]),
    reviewBasis: readString(record["review_basis"], "fixed_interval"),
    escalationPolicyRef: readNullableString(record["escalation_policy_ref"]),
    noReviewReason: readNullableString(record["no_review_reason"]),
  };
}

export function mapSourceDto(
  value: SourceDto | Record<string, unknown> | null | undefined,
): RiskControlSource {
  const record = asRecord(value);
  const snapshot = record["snapshot"];
  return {
    sourceType: readString(record["source_type"], "other"),
    sourceReference: readNullableString(record["source_reference"]),
    riskAssessmentId: readWrappedId(
      record["risk_assessment_id"] as WrappedIdDto | undefined,
    ),
    sourceControlReference: readNullableString(
      record["source_control_reference"],
    ),
    assessmentVersion:
      typeof record["assessment_version"] === "number"
        ? (record["assessment_version"] as number)
        : null,
    assessmentApprovedAt: readNullableString(record["assessment_approved_at"]),
    residualLevel: readNullableString(record["residual_level"]),
    snapshot:
      snapshot && typeof snapshot === "object" && !Array.isArray(snapshot)
        ? (snapshot as RiskControlSource["snapshot"])
        : null,
  };
}

export function mapRiskControlDto(dto: RiskControlDto): RiskControl {
  return {
    id: dto.id,
    organizationId: dto.organization_id,
    code: dto.code,
    title: dto.title,
    description: dto.description,
    hierarchyLevel: dto.hierarchy_level,
    controlNature: dto.control_nature,
    source: mapSourceDto(dto.source),
    hazardId: dto.hazard_id,
    riskAssessmentId: dto.risk_assessment_id,
    scope: dto.scope ?? [],
    owner: mapOwnerDto(dto.owner),
    implementation: mapImplementationDto(dto.implementation),
    evidence: (dto.evidence ?? []).map(mapEvidence),
    verifications: (dto.verifications ?? []).map(mapVerification),
    reviewSchedule: mapReviewScheduleDto(dto.review_schedule),
    competencyRequirements: dto.competency_requirements ?? [],
    relatedEntities: dto.related_entities ?? [],
    extensionData: dto.extension_data ?? {},
    status: dto.lifecycle_status,
    latestEffectivenessResult: dto.latest_effectiveness_result,
    nextReviewDate: dto.next_review_date,
    isOverdue: Boolean(dto.is_overdue),
    verificationMethodRequirement: readString(
      dto.verification_method_requirement,
    ),
    version: dto.version,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export function mapRiskControlListDto(
  dto: RiskControlListDto,
): RiskControlListResult {
  return {
    items: dto.items.map(mapRiskControlDto),
    pagination: dto.pagination,
  };
}

/** Backend appends verifications; the newest record is the last element. */
export function latestVerification(
  control: Pick<RiskControl, "verifications">,
): RiskControlVerification | null {
  return control.verifications.at(-1) ?? null;
}
