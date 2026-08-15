/** Backend transport DTOs — snake_case, match HazardsAPI. */

export type HazardStatusDto = "draft" | "active" | "archived";

export type HazardCategoryDto =
  | "physical"
  | "mechanical"
  | "electrical"
  | "chemical"
  | "biological"
  | "ergonomic"
  | "psychosocial"
  | "fire_and_explosion"
  | "thermal"
  | "radiation"
  | "pressure"
  | "work_at_height"
  | "confined_space"
  | "transport"
  | "environmental"
  | "dangerous_goods"
  | "process_safety"
  | "natural_hazard"
  | "organizational"
  | "other";

export type SafetyDirectionDto =
  | "occupational_safety"
  | "industrial_safety"
  | "fire_safety"
  | "environmental_safety"
  | "transport_safety"
  | "dangerous_goods_transport"
  | "civil_defense_and_emergency"
  | "sanitary_and_hygienic_safety"
  | "electrical_safety"
  | "radiation_safety";

export type HazardSourceDto =
  | "employee_report"
  | "inspection"
  | "incident_investigation"
  | "near_miss"
  | "risk_assessment"
  | "regulatory_assessment"
  | "audit"
  | "management_review"
  | "change_management"
  | "equipment_documentation"
  | "sout"
  | "production_control"
  | "environmental_monitoring"
  | "transport_control"
  | "other";

export type AffectedSubjectDto =
  | "employee"
  | "contractor"
  | "visitor"
  | "driver"
  | "passenger"
  | "public"
  | "environment"
  | "equipment"
  | "building"
  | "transport_vehicle"
  | "cargo"
  | "production_process";

export interface HazardDto {
  id: string;
  organization_id: string;
  code: string;
  title: string;
  description: string;
  category: HazardCategoryDto;
  safety_directions: SafetyDirectionDto[];
  source: HazardSourceDto;
  affected_subjects: AffectedSubjectDto[];
  location_reference: string | null;
  process_reference: string | null;
  equipment_reference: string | null;
  extension_references: Record<string, string>;
  status: HazardStatusDto;
  identified_at: string;
  identified_by: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  archived_at: string | null;
  archived_by: string | null;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface PaginationDto {
  total: number;
  offset: number;
  limit: number;
}

export interface HazardListDto {
  items: HazardDto[];
  pagination: PaginationDto;
}

export interface CreateHazardDto {
  code: string;
  title: string;
  description?: string;
  category: HazardCategoryDto;
  safety_directions: SafetyDirectionDto[];
  source: HazardSourceDto;
  affected_subjects?: AffectedSubjectDto[];
  location_reference?: string | null;
  process_reference?: string | null;
  equipment_reference?: string | null;
  extension_references?: Record<string, string>;
  identified_at?: string | null;
}

export interface UpdateHazardDto {
  expected_version: number;
  title?: string;
  description?: string;
  category?: HazardCategoryDto;
  safety_directions?: SafetyDirectionDto[];
  source?: HazardSourceDto;
  affected_subjects?: AffectedSubjectDto[];
  location_reference?: string | null;
  process_reference?: string | null;
  equipment_reference?: string | null;
  extension_references?: Record<string, string>;
}

export interface HazardListParams {
  offset?: number;
  limit?: number;
  status?: HazardStatusDto;
  category?: HazardCategoryDto;
  safety_direction?: SafetyDirectionDto;
  source?: HazardSourceDto;
  affected_subject?: AffectedSubjectDto;
  search?: string;
  include_archived?: boolean;
  identified_from?: string;
  identified_to?: string;
  created_from?: string;
  created_to?: string;
}

/** Frontend view model — camelCase. */
export interface Hazard {
  id: string;
  organizationId: string;
  code: string;
  title: string;
  description: string;
  category: HazardCategoryDto;
  safetyDirections: SafetyDirectionDto[];
  source: HazardSourceDto;
  affectedSubjects: AffectedSubjectDto[];
  locationReference: string | null;
  processReference: string | null;
  equipmentReference: string | null;
  extensionReferences: Record<string, string>;
  status: HazardStatusDto;
  identifiedAt: string;
  identifiedBy: string;
  reviewedAt: string | null;
  reviewedBy: string | null;
  archivedAt: string | null;
  archivedBy: string | null;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export interface HazardListResult {
  items: Hazard[];
  pagination: PaginationDto;
}

export interface RiskAssessmentSummary {
  id: string;
  code: string;
  title: string;
  status: string;
  assessmentProfile: string;
  inherentRiskLabel: string | null;
  residualRiskLabel: string | null;
  approvedAt: string | null;
  updatedAt: string;
}

export interface HazardActivityItem {
  id: string;
  title: string;
  occurredAt: string;
  actorUserId: string | null;
  action: string;
  outcome: string;
  eventName: string;
}

export type HazardLifecycleAction = "activate" | "archive" | "restore";

export interface HazardCapabilities {
  canRead: boolean;
  canCreate: boolean;
  canUpdate: boolean;
  canActivate: boolean;
  canArchive: boolean;
  canRestore: boolean;
  canViewRelatedAssessments: boolean;
  /** Create Risk Assessment entry point — uses risk:create, not a new permission. */
  canCreateRiskAssessment: boolean;
  canViewActivity: boolean;
}
