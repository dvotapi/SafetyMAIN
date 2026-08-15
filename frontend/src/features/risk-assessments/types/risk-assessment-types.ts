/** Backend transport DTOs — snake_case, match RiskAssessmentsAPI. */

export type RiskAssessmentStatusDto =
  "draft" | "under_review" | "approved" | "superseded" | "archived";

export type AssessmentProfileDto =
  | "simple_3x3"
  | "simple_5x5"
  | "corporate_custom"
  | "russian_occupational_risk"
  | "industrial_safety"
  | "fire_safety"
  | "environmental_risk"
  | "transport_risk"
  | "adr_risk";

export type AssessedObjectTypeDto =
  | "workplace"
  | "job_position"
  | "work_activity"
  | "equipment"
  | "vehicle"
  | "production_process"
  | "location"
  | "contractor_activity"
  | "chemical"
  | "emergency_scenario";

export type RiskLevelDto = "low" | "medium" | "high" | "extreme";

export type ControlTypeDto =
  "elimination" | "substitution" | "engineering" | "administrative" | "ppe";

export type AcceptanceDecisionDto =
  | "accepted"
  | "conditionally_accepted"
  | "not_accepted"
  | "requires_escalation";

export type RiskFactorId =
  | "probability"
  | "severity"
  | "exposure"
  | "frequency"
  | "detectability"
  | "environmental_impact"
  | "fire_consequence"
  | "business_impact";

export interface RiskFactorScoreDto {
  factor: string;
  score: number;
}

export interface RiskEvaluationDto {
  factors?: RiskFactorScoreDto[];
  level?: string | null;
  explanation?: string;
}

export interface ControlMeasureDto {
  id?: string | null;
  control_type: ControlTypeDto;
  description: string;
  responsible?: string | null;
  implemented: boolean;
  effective?: boolean | null;
}

export interface RiskAcceptanceDto {
  decision: AcceptanceDecisionDto;
  justification?: string;
  reviewer_id?: string | null;
  approved_at?: string | null;
}

export interface ReviewScheduleDto {
  review_due_date?: string | null;
  review_frequency_days?: number | null;
  review_reason?: string | null;
  triggered_by?: string | null;
}

export interface AssessedObjectDto {
  object_type: AssessedObjectTypeDto;
  reference: string;
}

export interface RiskAssessmentDto {
  id: string;
  organization_id: string;
  hazard_id: string;
  code: string;
  title: string;
  assessment_profile: AssessmentProfileDto | string;
  assessed_object: AssessedObjectDto | Record<string, unknown>;
  assessor_id: string;
  assessment_date: string;
  review_schedule: ReviewScheduleDto | Record<string, unknown>;
  inherent_risk: RiskEvaluationDto | null;
  residual_risk: RiskEvaluationDto | null;
  controls: ControlMeasureDto[];
  acceptance: RiskAcceptanceDto | null;
  competency_requirements: string[];
  extension_references: Record<string, string>;
  status: RiskAssessmentStatusDto;
  superseded_by_id: string | null;
  archived_at: string | null;
  archived_by: string | null;
  approved_at: string | null;
  approved_by: string | null;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface PaginationDto {
  total: number;
  offset: number;
  limit: number;
}

export interface RiskAssessmentListDto {
  items: RiskAssessmentDto[];
  pagination: PaginationDto;
}

export interface CreateRiskAssessmentDto {
  hazard_id: string;
  code: string;
  title: string;
  assessment_profile: AssessmentProfileDto;
  assessed_object: {
    object_type: AssessedObjectTypeDto;
    reference: string;
  };
  assessment_date?: string | null;
  review_schedule?: {
    review_due_date?: string | null;
    review_frequency_days?: number | null;
    review_reason?: string | null;
    triggered_by?: string | null;
  } | null;
  competency_requirements?: string[];
  extension_references?: Record<string, string>;
}

export interface RiskEvaluationRequestDto {
  probability?: string | number | null;
  severity?: string | number | null;
  factors?: RiskFactorScoreDto[];
  level?: RiskLevelDto | null;
  explanation?: string;
}

export interface UpdateRiskAssessmentDto {
  expected_version: number;
  title?: string;
  assessed_object?: {
    object_type: AssessedObjectTypeDto;
    reference: string;
  };
  assessment_date?: string | null;
  review_schedule?: {
    review_due_date?: string | null;
    review_frequency_days?: number | null;
    review_reason?: string | null;
    triggered_by?: string | null;
  } | null;
  competency_requirements?: string[];
  extension_references?: Record<string, string>;
  controls?: Array<{
    id?: string | null;
    control_type: ControlTypeDto;
    description: string;
    responsible?: string | null;
    implemented: boolean;
    effective?: boolean | null;
  }>;
  inherent_risk?: RiskEvaluationRequestDto | null;
  residual_risk?: RiskEvaluationRequestDto | null;
  acceptance?: {
    decision: AcceptanceDecisionDto;
    justification?: string;
    reviewer_id?: string | null;
  } | null;
  submit_for_review?: boolean;
}

export interface ApproveRiskAssessmentDto {
  expected_version: number;
  acceptance?: {
    decision: AcceptanceDecisionDto;
    justification?: string;
    reviewer_id?: string | null;
  } | null;
}

export interface ArchiveRiskAssessmentDto {
  expected_version: number;
  reason: string;
}

export interface RiskAssessmentListParams {
  offset?: number;
  limit?: number;
  hazard_id?: string;
  status?: RiskAssessmentStatusDto;
  assessment_profile?: AssessmentProfileDto;
  assessed_object_type?: AssessedObjectTypeDto;
  include_archived?: boolean;
  include_superseded?: boolean;
  search?: string;
  created_from?: string;
  created_to?: string;
}

/** Frontend view models — camelCase. */

export interface RiskFactorScore {
  factor: string;
  score: number;
}

export interface RiskEvaluation {
  factors: RiskFactorScore[];
  level: string | null;
  explanation: string;
}

export interface ControlMeasure {
  id: string | null;
  controlType: ControlTypeDto;
  description: string;
  responsible: string | null;
  implemented: boolean;
  effective: boolean | null;
}

export interface RiskAcceptance {
  decision: AcceptanceDecisionDto;
  justification: string;
  reviewerId: string | null;
  approvedAt: string | null;
}

export interface ReviewSchedule {
  reviewDueDate: string | null;
  reviewFrequencyDays: number | null;
  reviewReason: string | null;
  triggeredBy: string | null;
}

export interface AssessedObject {
  objectType: AssessedObjectTypeDto;
  reference: string;
}

export interface RiskAssessment {
  id: string;
  organizationId: string;
  hazardId: string;
  code: string;
  title: string;
  assessmentProfile: AssessmentProfileDto | string;
  assessedObject: AssessedObject;
  assessorId: string;
  assessmentDate: string;
  reviewSchedule: ReviewSchedule;
  inherentRisk: RiskEvaluation | null;
  residualRisk: RiskEvaluation | null;
  controls: ControlMeasure[];
  acceptance: RiskAcceptance | null;
  competencyRequirements: string[];
  extensionReferences: Record<string, string>;
  status: RiskAssessmentStatusDto;
  supersededById: string | null;
  archivedAt: string | null;
  archivedBy: string | null;
  approvedAt: string | null;
  approvedBy: string | null;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export interface RiskAssessmentListResult {
  items: RiskAssessment[];
  pagination: PaginationDto;
}

/** Minimal Hazard summary for RA-local hazard reads (selector / related). */
export interface RiskAssessmentHazardSummary {
  id: string;
  code: string;
  title: string;
  status: string;
}

export interface RelatedRiskControlSummary {
  id: string;
  code: string;
  title: string;
  hierarchyLevel: string;
  lifecycleStatus: string;
  ownerLabel: string | null;
  latestEffectivenessResult: string | null;
  nextReviewDate: string | null;
}

export interface RiskAssessmentActivityItem {
  id: string;
  title: string;
  occurredAt: string;
  actorUserId: string | null;
  action: string;
  outcome: string;
  eventName: string;
}

export type RiskAssessmentLifecycleAction =
  "submit_for_review" | "approve" | "archive";

export interface RiskAssessmentCapabilities {
  canRead: boolean;
  canCreate: boolean;
  canUpdateDraft: boolean;
  canSubmitForReview: boolean;
  canApprove: boolean;
  canArchive: boolean;
  canViewRelatedControls: boolean;
  canViewActivity: boolean;
}
