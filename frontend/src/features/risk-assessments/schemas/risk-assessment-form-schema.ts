import { z } from "zod";

import type {
  AcceptanceDecisionDto,
  AssessedObjectTypeDto,
  AssessmentProfileDto,
  ControlTypeDto,
} from "@/features/risk-assessments/types/risk-assessment-types";
import {
  getAssessmentProfileCatalogEntry,
  listAssessmentProfileCodes,
} from "@/features/risk-assessments/utils/assessment-profiles";
import { HIERARCHY_OF_CONTROLS } from "@/features/risk-assessments/utils/hierarchy-of-controls";

export const ASSESSMENT_PROFILES = listAssessmentProfileCodes();

/** Shared assessed-object type enum (schema + registry filters). */
export const ASSESSED_OBJECT_TYPES = [
  "workplace",
  "job_position",
  "work_activity",
  "equipment",
  "vehicle",
  "production_process",
  "location",
  "contractor_activity",
  "chemical",
  "emergency_scenario",
] as const satisfies readonly AssessedObjectTypeDto[];

export const CONTROL_TYPES = HIERARCHY_OF_CONTROLS;

export const ACCEPTANCE_DECISIONS = [
  "accepted",
  "conditionally_accepted",
  "not_accepted",
  "requires_escalation",
] as const satisfies readonly AcceptanceDecisionDto[];

const factorScoreSchema = z.number().int().min(1).max(5).nullable();

export const riskEvaluationFormSchema = z.object({
  probabilityScore: factorScoreSchema,
  severityScore: factorScoreSchema,
  /** Extra profile factors keyed by factor id (e.g. business_impact). */
  extraFactorScores: z.record(z.string(), factorScoreSchema),
  explanation: z.string().max(10_000),
});

export type RiskEvaluationFormValues = z.infer<typeof riskEvaluationFormSchema>;

/** True when the evaluation section has no user-entered scores or explanation. */
export function isRiskEvaluationFormEmpty(
  values: RiskEvaluationFormValues,
): boolean {
  const hasExtra = Object.values(values.extraFactorScores).some(
    (score) => score !== null && score !== undefined,
  );
  return (
    values.probabilityScore === null &&
    values.severityScore === null &&
    !hasExtra &&
    values.explanation.trim() === ""
  );
}

export const proposedControlFormSchema = z.object({
  id: z.string().nullable(),
  controlType: z.enum(
    CONTROL_TYPES as unknown as [ControlTypeDto, ...ControlTypeDto[]],
  ),
  description: z.string().trim().min(1, "Description is required").max(4000),
  responsible: z.string().max(512),
  implemented: z.boolean(),
  effective: z.boolean().nullable(),
});

function refineEvaluationSection(
  values: z.infer<typeof riskEvaluationFormSchema>,
  profileCode: AssessmentProfileDto,
  section: "inherentRisk" | "residualRisk",
  ctx: z.RefinementCtx,
): void {
  if (isRiskEvaluationFormEmpty(values)) {
    return;
  }

  const profile = getAssessmentProfileCatalogEntry(profileCode);
  const maxScore = profile?.matrixSize ?? 5;

  if (values.probabilityScore === null) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: [section, "probabilityScore"],
      message: "Probability is required when entering risk evaluation",
    });
  } else if (values.probabilityScore > maxScore) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: [section, "probabilityScore"],
      message: `Probability must be between 1 and ${maxScore} for this profile`,
    });
  }

  if (values.severityScore === null) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: [section, "severityScore"],
      message: "Severity is required when entering risk evaluation",
    });
  } else if (values.severityScore > maxScore) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: [section, "severityScore"],
      message: `Severity must be between 1 and ${maxScore} for this profile`,
    });
  }

  for (const [factorId, score] of Object.entries(values.extraFactorScores)) {
    if (score !== null && score !== undefined && score > maxScore) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [section, "extraFactorScores", factorId],
        message: `Score must be between 1 and ${maxScore} for this profile`,
      });
    }
  }

  if (!profile) {
    return;
  }

  for (const factorId of profile.requiredFactorIds) {
    if (factorId === "probability" || factorId === "severity") {
      continue;
    }
    const score = values.extraFactorScores[factorId];
    if (score === null || score === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [section, "extraFactorScores", factorId],
        message: `${factorId} is required for this assessment profile`,
      });
    } else if (score > maxScore) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [section, "extraFactorScores", factorId],
        message: `Score must be between 1 and ${maxScore} for this profile`,
      });
    }
  }
}

export const riskAssessmentFormSchema = z
  .object({
    hazardId: z.string().trim().min(1, "Hazard is required"),
    code: z.string().trim().min(1, "Code is required").max(64),
    title: z.string().trim().min(1, "Title is required").max(512),
    assessmentProfile: z.enum(
      ASSESSMENT_PROFILES as unknown as [
        AssessmentProfileDto,
        ...AssessmentProfileDto[],
      ],
    ),
    assessedObjectType: z.enum(ASSESSED_OBJECT_TYPES),
    assessedObjectReference: z
      .string()
      .trim()
      .min(1, "Assessed object reference is required")
      .max(256),
    assessmentDate: z.string(),
    reviewDueDate: z.string(),
    reviewFrequencyDays: z.string(),
    reviewReason: z.string().max(2000),
    reviewTriggeredBy: z.string().max(128),
    competencyRequirements: z.array(z.string().trim().min(1)).max(50),
    inherentRisk: riskEvaluationFormSchema,
    residualRisk: riskEvaluationFormSchema,
    controls: z.array(proposedControlFormSchema),
    acceptanceDecision: z.enum(ACCEPTANCE_DECISIONS).nullable(),
    acceptanceJustification: z.string().max(4000),
    acceptanceReviewerId: z.string(),
  })
  .superRefine((data, ctx) => {
    refineEvaluationSection(
      data.inherentRisk,
      data.assessmentProfile,
      "inherentRisk",
      ctx,
    );
    refineEvaluationSection(
      data.residualRisk,
      data.assessmentProfile,
      "residualRisk",
      ctx,
    );
  });

export type ProposedControlFormValues = z.infer<
  typeof proposedControlFormSchema
>;
export type RiskAssessmentFormValues = z.infer<typeof riskAssessmentFormSchema>;

export const emptyRiskEvaluationFormValues: RiskEvaluationFormValues = {
  probabilityScore: null,
  severityScore: null,
  extraFactorScores: {},
  explanation: "",
};

export const defaultRiskAssessmentFormValues: RiskAssessmentFormValues = {
  hazardId: "",
  code: "",
  title: "",
  assessmentProfile: "simple_5x5",
  assessedObjectType: "workplace",
  assessedObjectReference: "",
  assessmentDate: "",
  reviewDueDate: "",
  reviewFrequencyDays: "",
  reviewReason: "",
  reviewTriggeredBy: "",
  competencyRequirements: [],
  inherentRisk: { ...emptyRiskEvaluationFormValues },
  residualRisk: { ...emptyRiskEvaluationFormValues },
  controls: [],
  acceptanceDecision: null,
  acceptanceJustification: "",
  acceptanceReviewerId: "",
};
