import type {
  AssessedObject,
  AssessedObjectDto,
  AssessedObjectTypeDto,
  ControlMeasure,
  ControlMeasureDto,
  CreateRiskAssessmentDto,
  ReviewSchedule,
  ReviewScheduleDto,
  RiskAcceptance,
  RiskAcceptanceDto,
  RiskAssessment,
  RiskAssessmentDto,
  RiskAssessmentListDto,
  RiskAssessmentListResult,
  RiskEvaluation,
  RiskEvaluationDto,
  RiskEvaluationRequestDto,
  RiskFactorScore,
  UpdateRiskAssessmentDto,
} from "@/features/risk-assessments/types/risk-assessment-types";
import type {
  RiskAssessmentFormValues,
  RiskEvaluationFormValues,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import { emptyRiskEvaluationFormValues } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import { getAssessmentProfileCatalogEntry } from "@/features/risk-assessments/utils/assessment-profiles";

function emptyToUndefined(
  value: string | undefined | null,
): string | undefined {
  if (value === undefined || value === null) {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed.length === 0 ? undefined : trimmed;
}

/** Form date inputs are YYYY-MM-DD; backend datetime fields accept ISO datetime. */
function dateOnlyToApiDatetime(value: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return `${value}T00:00:00Z`;
  }
  return value;
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function mapFactorScores(value: unknown): RiskFactorScore[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.flatMap((item) => {
    if (!item || typeof item !== "object") {
      return [];
    }
    const record = item as Record<string, unknown>;
    const factor = record["factor"];
    const score = record["score"];
    if (typeof factor !== "string" || typeof score !== "number") {
      return [];
    }
    return [{ factor, score }];
  });
}

export function mapRiskEvaluationDto(
  dto: RiskEvaluationDto | null | undefined,
): RiskEvaluation | null {
  if (!dto) {
    return null;
  }
  return {
    factors: mapFactorScores(dto.factors),
    level: typeof dto.level === "string" ? dto.level : null,
    explanation: typeof dto.explanation === "string" ? dto.explanation : "",
  };
}

export function evaluationToFormValues(
  evaluation: RiskEvaluation | null | undefined,
): RiskEvaluationFormValues {
  if (!evaluation) {
    return { ...emptyRiskEvaluationFormValues, extraFactorScores: {} };
  }
  const extraFactorScores: Record<string, number | null> = {};
  let probabilityScore: number | null = null;
  let severityScore: number | null = null;
  for (const factor of evaluation.factors) {
    if (factor.factor === "probability") {
      probabilityScore = factor.score;
      continue;
    }
    if (factor.factor === "severity") {
      severityScore = factor.score;
      continue;
    }
    extraFactorScores[factor.factor] = factor.score;
  }
  return {
    probabilityScore,
    severityScore,
    extraFactorScores,
    explanation: evaluation.explanation,
  };
}

/**
 * Rebuilds a PATCH evaluation payload from form scores.
 * Requires both probability and severity; otherwise returns null.
 * Does not set authoritative `level` — backend calculates it.
 */
export function formValuesToEvaluationRequest(
  values: RiskEvaluationFormValues,
  profileCode?: string,
): RiskEvaluationRequestDto | null {
  if (values.probabilityScore === null || values.severityScore === null) {
    return null;
  }

  const probabilityScore = values.probabilityScore;
  const severityScore = values.severityScore;
  const extraEntries = Object.entries(values.extraFactorScores).filter(
    ([, score]) => score !== null && score !== undefined,
  ) as Array<[string, number]>;
  const explanation = values.explanation.trim();

  const factors: Array<{ factor: string; score: number }> = [
    { factor: "probability", score: probabilityScore },
    { factor: "severity", score: severityScore },
  ];
  for (const [factor, score] of extraEntries) {
    factors.push({ factor, score });
  }

  const profile = profileCode
    ? getAssessmentProfileCatalogEntry(profileCode)
    : undefined;
  if (profile) {
    for (const factorId of profile.requiredFactorIds) {
      if (factorId === "probability" || factorId === "severity") {
        continue;
      }
      if (!factors.some((item) => item.factor === factorId)) {
        const score = values.extraFactorScores[factorId];
        if (typeof score === "number") {
          factors.push({ factor: factorId, score });
        }
      }
    }
  }

  return {
    explanation,
    factors,
    probability: probabilityScore,
    severity: severityScore,
  };
}

function mapAssessedObject(
  value: AssessedObjectDto | Record<string, unknown>,
): AssessedObject {
  const record = asRecord(value);
  const objectType = String(
    record["object_type"] ?? "workplace",
  ) as AssessedObjectTypeDto;
  const reference = String(record["reference"] ?? "");
  return { objectType, reference };
}

function mapReviewSchedule(
  value: ReviewScheduleDto | Record<string, unknown> | null | undefined,
): ReviewSchedule {
  const record = asRecord(value);
  const frequency = record["review_frequency_days"];
  return {
    reviewDueDate:
      typeof record["review_due_date"] === "string"
        ? record["review_due_date"]
        : null,
    reviewFrequencyDays: typeof frequency === "number" ? frequency : null,
    reviewReason:
      typeof record["review_reason"] === "string"
        ? record["review_reason"]
        : null,
    triggeredBy:
      typeof record["triggered_by"] === "string"
        ? record["triggered_by"]
        : null,
  };
}

function mapControl(dto: ControlMeasureDto): ControlMeasure {
  return {
    id: dto.id ?? null,
    controlType: dto.control_type,
    description: dto.description,
    responsible: dto.responsible ?? null,
    implemented: Boolean(dto.implemented),
    effective: dto.effective ?? null,
  };
}

function mapAcceptance(
  dto: RiskAcceptanceDto | null | undefined,
): RiskAcceptance | null {
  if (!dto) {
    return null;
  }
  return {
    decision: dto.decision,
    justification: dto.justification ?? "",
    reviewerId: dto.reviewer_id ?? null,
    approvedAt: dto.approved_at ?? null,
  };
}

export function mapRiskAssessmentDto(dto: RiskAssessmentDto): RiskAssessment {
  return {
    id: dto.id,
    organizationId: dto.organization_id,
    hazardId: dto.hazard_id,
    code: dto.code,
    title: dto.title,
    assessmentProfile: dto.assessment_profile,
    assessedObject: mapAssessedObject(dto.assessed_object),
    assessorId: dto.assessor_id,
    assessmentDate: dto.assessment_date,
    reviewSchedule: mapReviewSchedule(dto.review_schedule),
    inherentRisk: mapRiskEvaluationDto(dto.inherent_risk),
    residualRisk: mapRiskEvaluationDto(dto.residual_risk),
    controls: (dto.controls ?? []).map(mapControl),
    acceptance: mapAcceptance(dto.acceptance),
    competencyRequirements: dto.competency_requirements ?? [],
    extensionReferences: dto.extension_references ?? {},
    status: dto.status,
    supersededById: dto.superseded_by_id,
    archivedAt: dto.archived_at,
    archivedBy: dto.archived_by,
    approvedAt: dto.approved_at,
    approvedBy: dto.approved_by,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
    version: dto.version,
  };
}

export function mapRiskAssessmentListDto(
  dto: RiskAssessmentListDto,
): RiskAssessmentListResult {
  return {
    items: dto.items.map(mapRiskAssessmentDto),
    pagination: dto.pagination,
  };
}

function reviewScheduleFromForm(values: RiskAssessmentFormValues) {
  const reviewDueDate = emptyToUndefined(values.reviewDueDate);
  const reviewReason = emptyToUndefined(values.reviewReason);
  const triggeredBy = emptyToUndefined(values.reviewTriggeredBy);
  const frequencyRaw = values.reviewFrequencyDays.trim();
  const reviewFrequencyDays = frequencyRaw
    ? Number.parseInt(frequencyRaw, 10)
    : undefined;
  if (
    !reviewDueDate &&
    !reviewReason &&
    !triggeredBy &&
    (reviewFrequencyDays === undefined || Number.isNaN(reviewFrequencyDays))
  ) {
    return undefined;
  }
  return {
    review_due_date: reviewDueDate
      ? dateOnlyToApiDatetime(reviewDueDate)
      : null,
    review_frequency_days:
      reviewFrequencyDays !== undefined && !Number.isNaN(reviewFrequencyDays)
        ? reviewFrequencyDays
        : null,
    review_reason: reviewReason ?? null,
    triggered_by: triggeredBy ?? null,
  };
}

/** Create body — CreateRiskAssessmentRequest fields only. */
export function formValuesToCreateRequest(
  values: RiskAssessmentFormValues,
): CreateRiskAssessmentDto {
  const body: CreateRiskAssessmentDto = {
    hazard_id: values.hazardId.trim(),
    code: values.code.trim(),
    title: values.title.trim(),
    assessment_profile: values.assessmentProfile,
    assessed_object: {
      object_type: values.assessedObjectType,
      reference: values.assessedObjectReference.trim(),
    },
  };
  const assessmentDate = emptyToUndefined(values.assessmentDate);
  if (assessmentDate) {
    body.assessment_date = dateOnlyToApiDatetime(assessmentDate);
  }
  const schedule = reviewScheduleFromForm(values);
  if (schedule) {
    body.review_schedule = schedule;
  }
  if (values.competencyRequirements.length > 0) {
    body.competency_requirements = values.competencyRequirements.map((item) =>
      item.trim(),
    );
  }
  return body;
}

export function riskAssessmentToFormValues(
  assessment: RiskAssessment,
): RiskAssessmentFormValues {
  return {
    hazardId: assessment.hazardId,
    code: assessment.code,
    title: assessment.title,
    assessmentProfile:
      typeof assessment.assessmentProfile === "string"
        ? (assessment.assessmentProfile as RiskAssessmentFormValues["assessmentProfile"])
        : "simple_5x5",
    assessedObjectType: assessment.assessedObject.objectType,
    assessedObjectReference: assessment.assessedObject.reference,
    assessmentDate: assessment.assessmentDate
      ? assessment.assessmentDate.slice(0, 10)
      : "",
    reviewDueDate: assessment.reviewSchedule.reviewDueDate
      ? assessment.reviewSchedule.reviewDueDate.slice(0, 10)
      : "",
    reviewFrequencyDays:
      assessment.reviewSchedule.reviewFrequencyDays !== null
        ? String(assessment.reviewSchedule.reviewFrequencyDays)
        : "",
    reviewReason: assessment.reviewSchedule.reviewReason ?? "",
    reviewTriggeredBy: assessment.reviewSchedule.triggeredBy ?? "",
    competencyRequirements: [...assessment.competencyRequirements],
    inherentRisk: evaluationToFormValues(assessment.inherentRisk),
    residualRisk: evaluationToFormValues(assessment.residualRisk),
    controls: assessment.controls.map((control) => ({
      id: control.id,
      controlType: control.controlType,
      description: control.description,
      responsible: control.responsible ?? "",
      implemented: control.implemented,
      effective: control.effective,
    })),
    acceptanceDecision: assessment.acceptance?.decision ?? null,
    acceptanceJustification: assessment.acceptance?.justification ?? "",
    acceptanceReviewerId: assessment.acceptance?.reviewerId ?? "",
  };
}

export function formValuesToUpdateRequest(
  values: RiskAssessmentFormValues,
  expectedVersion: number,
  options?: { submitForReview?: boolean; includeRiskInputs?: boolean },
): UpdateRiskAssessmentDto {
  const includeRiskInputs = options?.includeRiskInputs ?? true;
  const body: UpdateRiskAssessmentDto = {
    expected_version: expectedVersion,
    title: values.title.trim(),
    assessed_object: {
      object_type: values.assessedObjectType,
      reference: values.assessedObjectReference.trim(),
    },
  };
  const assessmentDate = emptyToUndefined(values.assessmentDate);
  body.assessment_date = assessmentDate
    ? dateOnlyToApiDatetime(assessmentDate)
    : null;
  const schedule = reviewScheduleFromForm(values);
  body.review_schedule = schedule ?? null;
  body.competency_requirements = values.competencyRequirements.map((item) =>
    item.trim(),
  );

  if (includeRiskInputs) {
    body.controls = values.controls.map((control) => ({
      id: control.id,
      control_type: control.controlType,
      description: control.description.trim(),
      responsible: emptyToUndefined(control.responsible) ?? null,
      implemented: control.implemented,
      effective: control.effective,
    }));
    body.inherent_risk = formValuesToEvaluationRequest(
      values.inherentRisk,
      values.assessmentProfile,
    );
    body.residual_risk = formValuesToEvaluationRequest(
      values.residualRisk,
      values.assessmentProfile,
    );
    if (values.acceptanceDecision) {
      body.acceptance = {
        decision: values.acceptanceDecision,
        justification: values.acceptanceJustification.trim(),
        reviewer_id: emptyToUndefined(values.acceptanceReviewerId) ?? null,
      };
    }
  }

  if (options?.submitForReview) {
    body.submit_for_review = true;
  }
  return body;
}
