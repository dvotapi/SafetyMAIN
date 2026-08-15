/** Backend transport DTOs — snake_case, mirror backend/api/schemas/risk_controls.py. */

export type RiskControlStatusDto =
  | "draft"
  | "planned"
  | "in_implementation"
  | "implemented"
  | "verified_effective"
  | "verified_ineffective"
  | "suspended"
  | "superseded"
  | "archived"
  | "cancelled";

export type ControlTypeDto =
  | "elimination"
  | "substitution"
  | "engineering"
  | "administrative"
  | "ppe";

export type ControlNatureDto =
  "preventive" | "detective" | "mitigating" | "recovery";

export type EffectivenessResultDto =
  | "effective"
  | "partially_effective"
  | "ineffective"
  | "not_verified"
  | "not_applicable";

/** Results the domain accepts when recording a verification. */
export type VerifiableEffectivenessResultDto =
  "effective" | "partially_effective" | "ineffective";

export type OwnerTypeDto =
  | "user"
  | "employee"
  | "role"
  | "organizational_unit"
  | "external_party";

export type EvidenceTypeDto =
  | "document"
  | "photo"
  | "video"
  | "inspection_record"
  | "test_result"
  | "work_order"
  | "training_record"
  | "certificate"
  | "measurement"
  | "approval"
  | "other";

export type VerificationTypeDto =
  | "initial"
  | "scheduled_review"
  | "post_incident"
  | "post_inspection"
  | "post_change"
  | "management_review"
  | "other";

export type ReviewBasisDto =
  | "fixed_interval"
  | "risk_based"
  | "regulatory_requirement"
  | "manufacturer_requirement"
  | "corporate_policy"
  | "post_incident"
  | "post_change"
  | "manual";

export type MilestoneStatusDto =
  "pending" | "in_progress" | "completed" | "blocked" | "cancelled";

/** Some UserId/RiskAssessmentId fields serialize wrapped as {"value": uuid}. */
export type WrappedIdDto = { value: string } | string | null;

export interface ScopeReferenceDto {
  scope_type: string;
  reference: string;
}

export interface OwnerDto {
  owner_type: OwnerTypeDto | string;
  owner_reference: string;
  display_name_snapshot: string;
  /** ISO datetime. */
  assigned_at: string | null;
  /** Flat uuid string here, unlike other UserId fields. */
  assigned_by: string | null;
}

export interface MilestoneDto {
  id?: string | null;
  title: string;
  description?: string;
  due_date?: string | null;
  status?: MilestoneStatusDto | string;
  completed_at?: string | null;
  evidence_refs?: string[];
}

export interface ImplementationDto {
  target_start_date?: string | null;
  target_completion_date?: string | null;
  actual_start_date?: string | null;
  actual_completion_date?: string | null;
  implementation_method?: string;
  milestones?: MilestoneDto[];
  dependencies?: string[];
  resource_notes?: string;
  evidence_requirements?: string[];
  progress?: number;
  summary?: string;
  evidence_waiver_reason?: string | null;
}

export interface EvidenceDto {
  id: string;
  evidence_type: EvidenceTypeDto | string;
  external_reference: string;
  title: string;
  description?: string;
  captured_at?: string | null;
  captured_by?: WrappedIdDto;
  checksum?: string | null;
  metadata?: Record<string, string>;
}

export interface VerificationDto {
  id: string;
  verification_type: VerificationTypeDto | string;
  method: string;
  criteria?: string;
  performed_at?: string | null;
  performed_by?: WrappedIdDto;
  result: EffectivenessResultDto | string;
  rating?: string | null;
  findings?: string;
  evidence_refs?: string[];
  related_inspection_id?: string | null;
  related_incident_id?: string | null;
  next_action?: string | null;
  next_review_date?: string | null;
  profile_key?: string;
  profile_version?: string;
}

export interface ReviewScheduleDto {
  review_required?: boolean;
  review_frequency_days?: number | null;
  next_review_date?: string | null;
  last_review_date?: string | null;
  review_basis?: ReviewBasisDto | string;
  escalation_policy_ref?: string | null;
  no_review_reason?: string | null;
}

/** Immutable snapshot of the proposed control that produced this control. */
export interface SourceSnapshotDto {
  id?: string | null;
  control_type?: string;
  description?: string;
  responsible?: string | null;
  implemented?: boolean;
  effective?: boolean | null;
  [key: string]: unknown;
}

export interface SourceDto {
  source_type: string;
  source_reference?: string | null;
  /** Wrapped as {"value": uuid} when present. */
  risk_assessment_id?: WrappedIdDto;
  source_control_reference?: string | null;
  assessment_version?: number | null;
  assessment_approved_at?: string | null;
  residual_level?: string | null;
  snapshot?: SourceSnapshotDto | null;
}

export interface CompetencyRequirementDto {
  competency_ref: string;
  requirement_type: string;
  required_level?: string | null;
  training_program_ref?: string | null;
  notes?: string;
}

export interface RelatedEntityDto {
  entity_type: string;
  reference: string;
}

export interface RiskControlDto {
  id: string;
  organization_id: string;
  code: string;
  title: string;
  description: string;
  hierarchy_level: ControlTypeDto | string;
  control_nature: ControlNatureDto | string;
  source: SourceDto | Record<string, unknown>;
  hazard_id: string | null;
  risk_assessment_id: string | null;
  scope: ScopeReferenceDto[];
  owner: OwnerDto | null;
  implementation: ImplementationDto | Record<string, unknown>;
  evidence: EvidenceDto[];
  verifications: VerificationDto[];
  review_schedule: ReviewScheduleDto | Record<string, unknown>;
  competency_requirements: CompetencyRequirementDto[];
  related_entities: RelatedEntityDto[];
  extension_data: Record<string, unknown>;
  lifecycle_status: RiskControlStatusDto;
  latest_effectiveness_result: EffectivenessResultDto | string | null;
  next_review_date: string | null;
  /** Backend-authoritative overdue flag (added by TASK-P9-007a). */
  is_overdue: boolean;
  verification_method_requirement: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface PaginationDto {
  total: number;
  offset: number;
  limit: number;
}

export interface RiskControlListDto {
  items: RiskControlDto[];
  pagination: PaginationDto;
}

export interface RiskControlListParams {
  offset?: number;
  limit?: number;
  status?: RiskControlStatusDto;
  hierarchy_level?: ControlTypeDto;
  control_nature?: ControlNatureDto;
  hazard_id?: string;
  risk_assessment_id?: string;
  owner_reference?: string;
  latest_effectiveness_result?: EffectivenessResultDto;
  review_due_before?: string;
  review_due_after?: string;
  overdue_only?: boolean;
  awaiting_verification?: boolean;
  include_terminal?: boolean;
  search?: string;
}
