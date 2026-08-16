import type {
  CompetencyRequirementDto,
  ControlNatureDto,
  ControlTypeDto,
  EffectivenessResultDto,
  EvidenceTypeDto,
  MilestoneStatusDto,
  OwnerTypeDto,
  PaginationDto,
  RelatedEntityDto,
  ReviewBasisDto,
  RiskControlStatusDto,
  ScopeReferenceDto,
  SourceSnapshotDto,
  VerificationTypeDto,
} from "@/features/risk-controls/types/risk-control-dto";

/** Frontend view models — camelCase. */

export interface RiskControlOwner {
  ownerType: OwnerTypeDto | string;
  ownerReference: string;
  displayNameSnapshot: string;
  assignedAt: string | null;
  assignedBy: string | null;
  /** Snapshot if present, else the raw reference. Never empty when owner exists. */
  label: string;
}

export interface RiskControlMilestone {
  id: string | null;
  title: string;
  description: string;
  dueDate: string | null;
  status: MilestoneStatusDto | string;
  completedAt: string | null;
  evidenceRefs: string[];
}

export interface RiskControlImplementation {
  targetStartDate: string | null;
  targetCompletionDate: string | null;
  actualStartDate: string | null;
  actualCompletionDate: string | null;
  implementationMethod: string;
  milestones: RiskControlMilestone[];
  dependencies: string[];
  resourceNotes: string;
  evidenceRequirements: string[];
  progress: number;
  summary: string;
  evidenceWaiverReason: string | null;
}

export interface RiskControlEvidence {
  id: string;
  evidenceType: EvidenceTypeDto | string;
  externalReference: string;
  title: string;
  description: string;
  capturedAt: string | null;
  capturedByUserId: string | null;
  checksum: string | null;
  metadata: Record<string, string>;
}

export interface RiskControlVerification {
  id: string;
  verificationType: VerificationTypeDto | string;
  method: string;
  criteria: string;
  performedAt: string | null;
  performedByUserId: string | null;
  result: EffectivenessResultDto | string;
  rating: string | null;
  findings: string;
  evidenceRefs: string[];
  nextAction: string | null;
  nextReviewDate: string | null;
  profileKey: string;
  profileVersion: string;
}

export interface RiskControlReviewSchedule {
  reviewRequired: boolean;
  reviewFrequencyDays: number | null;
  nextReviewDate: string | null;
  lastReviewDate: string | null;
  reviewBasis: ReviewBasisDto | string;
  escalationPolicyRef: string | null;
  noReviewReason: string | null;
}

export interface RiskControlSource {
  sourceType: string;
  sourceReference: string | null;
  riskAssessmentId: string | null;
  sourceControlReference: string | null;
  assessmentVersion: number | null;
  assessmentApprovedAt: string | null;
  residualLevel: string | null;
  /** Immutable; rendered read-only and never reconstructed from live data. */
  snapshot: SourceSnapshotDto | null;
}

export interface RiskControl {
  id: string;
  organizationId: string;
  code: string;
  title: string;
  description: string;
  hierarchyLevel: ControlTypeDto | string;
  controlNature: ControlNatureDto | string;
  source: RiskControlSource;
  hazardId: string | null;
  riskAssessmentId: string | null;
  scope: ScopeReferenceDto[];
  owner: RiskControlOwner | null;
  implementation: RiskControlImplementation;
  evidence: RiskControlEvidence[];
  /** Append-only, oldest first. Latest is the last element. */
  verifications: RiskControlVerification[];
  reviewSchedule: RiskControlReviewSchedule;
  competencyRequirements: CompetencyRequirementDto[];
  relatedEntities: RelatedEntityDto[];
  extensionData: Record<string, unknown>;
  status: RiskControlStatusDto;
  latestEffectivenessResult: EffectivenessResultDto | string | null;
  nextReviewDate: string | null;
  /** Backend-authoritative; never recomputed client-side. */
  isOverdue: boolean;
  verificationMethodRequirement: string;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface RiskControlListResult {
  items: RiskControl[];
  pagination: PaginationDto;
}

/** Minimal cross-feature summaries — read via RC-local lite clients. */
export interface RiskControlHazardSummary {
  id: string;
  code: string;
  title: string;
  status: string;
}

export interface RiskControlAssessmentSummary {
  id: string;
  code: string;
  title: string;
  status: string;
}

export interface RiskControlActivityItem {
  id: string;
  title: string;
  occurredAt: string;
  actorUserId: string | null;
  action: string;
  outcome: string;
  eventName: string;
}

export type RiskControlLifecycleAction =
  | "assign_owner"
  | "plan"
  | "start_implementation"
  | "update_progress"
  | "add_evidence"
  | "complete_implementation"
  | "verify"
  | "schedule_review"
  | "complete_review"
  | "suspend"
  | "resume"
  | "supersede"
  | "cancel"
  | "archive";

export interface RiskControlCapabilities {
  canRead: boolean;
  canCreate: boolean;
  canUpdate: boolean;
  canAssignOwner: boolean;
  canImplement: boolean;
  canVerify: boolean;
  canReview: boolean;
  canSuspend: boolean;
  canSupersede: boolean;
  canArchive: boolean;
  canCancel: boolean;
  canMaterialize: boolean;
  canViewHazard: boolean;
  canViewAssessment: boolean;
  canViewActivity: boolean;
}
