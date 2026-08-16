import type { Meta, StoryObj } from "@storybook/react";

import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
import { EffectivenessSummary } from "@/features/risk-controls/components/effectiveness-summary";
import { EvidenceList } from "@/features/risk-controls/components/evidence-list";
import { ImplementationPlanSection } from "@/features/risk-controls/components/implementation-plan-section";
import { ImplementationProgressSection } from "@/features/risk-controls/components/implementation-progress-section";
import { ReviewScheduleSection } from "@/features/risk-controls/components/review-schedule-section";
import { RiskControlLifecycleActions } from "@/features/risk-controls/components/risk-control-lifecycle-actions";
import { RiskControlSummary } from "@/features/risk-controls/components/risk-control-summary";
import { SourceSnapshot } from "@/features/risk-controls/components/source-snapshot";
import { VerificationForm } from "@/features/risk-controls/components/verification-form";
import { VerificationHistory } from "@/features/risk-controls/components/verification-history";
import type {
  RiskControl,
  RiskControlCapabilities,
  RiskControlEvidence,
  RiskControlMilestone,
  RiskControlOwner,
  RiskControlReviewSchedule,
  RiskControlSource,
  RiskControlVerification,
} from "@/features/risk-controls/types/risk-control-types";

/* ----------------------------------------------------------------------
 * Deterministic fixtures — fixed UUIDs and ISO timestamps only, never
 * Date.now()/Math.random(), so Storybook snapshots are stable.
 * ---------------------------------------------------------------------- */

const CONTROL_ID = "10101010-1010-4010-8010-101010101010";
const HAZARD_ID = "30303030-3030-4030-8030-303030303030";
const RISK_ASSESSMENT_ID = "40404040-4040-4040-8040-404040404040";
const ORG_ID = "20202020-2020-4020-8020-202020202020";

const sampleOwner: RiskControlOwner = {
  ownerType: "user",
  ownerReference: "user-42",
  displayNameSnapshot: "Jane Doe",
  assignedAt: "2026-01-05T09:00:00Z",
  assignedBy: "user-1",
  label: "Jane Doe",
};

const sampleMilestone: RiskControlMilestone = {
  id: "milestone-1",
  title: "Install guarding",
  description: "Fabricate and install fixed guard on the conveyor pinch point.",
  dueDate: "2026-02-01",
  status: "completed",
  completedAt: "2026-01-28T00:00:00Z",
  evidenceRefs: ["EV-1"],
};

const sampleEvidence: RiskControlEvidence[] = [
  {
    id: "evidence-1",
    evidenceType: "photo",
    externalReference: "DMS-1001",
    title: "Guard installation photo",
    description: "Photo of the completed guard.",
    capturedAt: "2026-01-28T00:00:00Z",
    capturedByUserId: "user-42",
    checksum: null,
    metadata: {},
  },
  {
    id: "evidence-2",
    evidenceType: "inspection_record",
    externalReference: "INSP-2002",
    title: "Post-install inspection",
    description: "Inspection confirming guard meets spec.",
    capturedAt: "2026-01-29T00:00:00Z",
    capturedByUserId: "user-7",
    checksum: "sha256:abc123",
    metadata: {},
  },
];

function buildVerification(
  overrides: Partial<RiskControlVerification> = {},
): RiskControlVerification {
  return {
    id: "verification-1",
    verificationType: "initial",
    method: "Field inspection",
    criteria: "Guard prevents hand access to pinch point.",
    performedAt: "2026-02-05T00:00:00Z",
    performedByUserId: "user-7",
    result: "effective",
    rating: null,
    findings: "Guard verified in place and functioning as intended.",
    evidenceRefs: ["EV-1"],
    nextAction: null,
    nextReviewDate: "2027-02-05",
    profileKey: "default",
    profileVersion: "1",
    ...overrides,
  };
}

const sampleVerificationHistory: RiskControlVerification[] = [
  buildVerification({
    id: "verification-1",
    performedAt: "2026-02-05T00:00:00Z",
    result: "effective",
  }),
  buildVerification({
    id: "verification-2",
    performedAt: "2026-05-05T00:00:00Z",
    result: "partially_effective",
    findings: "Guard shows minor wear; partial gap observed.",
  }),
  buildVerification({
    id: "verification-3",
    performedAt: "2026-08-05T00:00:00Z",
    result: "ineffective",
    findings: "Guard was found removed during production changeover.",
  }),
];

const scheduledReviewSchedule: RiskControlReviewSchedule = {
  reviewRequired: true,
  reviewFrequencyDays: 365,
  nextReviewDate: "2027-02-05",
  lastReviewDate: "2026-02-05",
  reviewBasis: "fixed_interval",
  escalationPolicyRef: "ESC-SAFETY-1",
  noReviewReason: null,
};

const noReviewSchedule: RiskControlReviewSchedule = {
  reviewRequired: false,
  reviewFrequencyDays: null,
  nextReviewDate: null,
  lastReviewDate: null,
  reviewBasis: "manual",
  escalationPolicyRef: null,
  noReviewReason:
    "Control is a one-time engineering fix with no recurring failure mode.",
};

const overdueReviewSchedule: RiskControlReviewSchedule = {
  reviewRequired: true,
  reviewFrequencyDays: 365,
  nextReviewDate: "2026-06-01",
  lastReviewDate: "2025-06-01",
  reviewBasis: "risk_based",
  escalationPolicyRef: null,
  noReviewReason: null,
};

const presentSource: RiskControlSource = {
  sourceType: "risk_assessment",
  sourceReference: "RA-100/control-0",
  riskAssessmentId: RISK_ASSESSMENT_ID,
  sourceControlReference: "control-0",
  assessmentVersion: 2,
  assessmentApprovedAt: "2026-01-02T00:00:00Z",
  residualLevel: "medium",
  snapshot: {
    control_type: "engineering",
    description: "Install guard rail on conveyor",
    responsible: "Maintenance team",
  },
};

const absentSource: RiskControlSource = {
  sourceType: "manual",
  sourceReference: null,
  riskAssessmentId: null,
  sourceControlReference: null,
  assessmentVersion: null,
  assessmentApprovedAt: null,
  residualLevel: null,
  snapshot: null,
};

const FULL_CAPABILITIES: RiskControlCapabilities = {
  canRead: true,
  canCreate: true,
  canUpdate: true,
  canAssignOwner: true,
  canImplement: true,
  canVerify: true,
  canReview: true,
  canSuspend: true,
  canSupersede: true,
  canArchive: true,
  canCancel: true,
  canMaterialize: true,
  canViewHazard: true,
  canViewAssessment: true,
  canViewActivity: true,
};

const READ_ONLY_CAPABILITIES: RiskControlCapabilities = {
  ...FULL_CAPABILITIES,
  canUpdate: false,
  canAssignOwner: false,
  canImplement: false,
  canVerify: false,
  canReview: false,
  canSuspend: false,
  canSupersede: false,
  canArchive: false,
  canCancel: false,
};

function buildControl(overrides: Partial<RiskControl> = {}): RiskControl {
  return {
    id: CONTROL_ID,
    organizationId: ORG_ID,
    code: "RC-0100",
    title: "Install machine guarding on conveyor pinch point",
    description: "Fixed guard on the conveyor pinch point.",
    hierarchyLevel: "engineering",
    controlNature: "preventive",
    source: absentSource,
    hazardId: HAZARD_ID,
    riskAssessmentId: RISK_ASSESSMENT_ID,
    scope: [],
    owner: sampleOwner,
    implementation: {
      targetStartDate: "2026-01-10",
      targetCompletionDate: "2026-02-01",
      actualStartDate: "2026-01-10T00:00:00Z",
      actualCompletionDate: null,
      implementationMethod: "Contracted fabrication and install",
      milestones: [sampleMilestone],
      dependencies: ["Vendor quote approval"],
      resourceNotes: "Requires a half-day production stoppage.",
      evidenceRequirements: ["Post-install inspection record"],
      progress: 60,
      summary: "",
      evidenceWaiverReason: null,
    },
    evidence: [],
    verifications: [],
    reviewSchedule: scheduledReviewSchedule,
    competencyRequirements: [],
    relatedEntities: [],
    extensionData: {},
    status: "in_implementation",
    latestEffectivenessResult: null,
    nextReviewDate: scheduledReviewSchedule.nextReviewDate,
    isOverdue: false,
    verificationMethodRequirement: "Visual inspection",
    version: 4,
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-10T00:00:00Z",
    ...overrides,
  };
}

const meta: Meta = {
  title: "Features/RiskControls",
};

export default meta;

/* ----------------------------------------------------------------------
 * RiskControlSummary
 * ---------------------------------------------------------------------- */

export const Summary: StoryObj = {
  render: () => <RiskControlSummary control={buildControl()} />,
};

/* ----------------------------------------------------------------------
 * ControlOwnerSection — assigned / unassigned / read-only
 * ---------------------------------------------------------------------- */

export const OwnerAssigned: StoryObj = {
  render: () => (
    <ControlOwnerSection
      owner={sampleOwner}
      status="in_implementation"
      version={4}
      capabilities={FULL_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onAssign={() => undefined}
    />
  ),
};

export const OwnerUnassigned: StoryObj = {
  render: () => (
    <ControlOwnerSection
      owner={null}
      status="draft"
      version={1}
      capabilities={FULL_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onAssign={() => undefined}
    />
  ),
};

export const OwnerReadOnly: StoryObj = {
  render: () => (
    <ControlOwnerSection
      owner={sampleOwner}
      status="in_implementation"
      version={4}
      capabilities={READ_ONLY_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onAssign={() => undefined}
    />
  ),
};

export const OwnerAssignForm: StoryObj = {
  render: () => (
    <ControlOwnerSection
      owner={null}
      status="draft"
      version={1}
      capabilities={FULL_CAPABILITIES}
      open
      onOpenChange={() => undefined}
      onAssign={() => undefined}
    />
  ),
};

/* ----------------------------------------------------------------------
 * ImplementationPlanSection — empty (blocked, no owner) / planned (ready)
 * ---------------------------------------------------------------------- */

export const ImplementationPlanEmpty: StoryObj = {
  render: () => (
    <ImplementationPlanSection
      status="draft"
      ownerAssigned={false}
      version={1}
      verificationMethodRequirement=""
      capabilities={FULL_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onPlan={() => undefined}
    />
  ),
};

export const ImplementationPlanReady: StoryObj = {
  render: () => (
    <ImplementationPlanSection
      status="draft"
      ownerAssigned
      version={1}
      verificationMethodRequirement=""
      capabilities={FULL_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onPlan={() => undefined}
    />
  ),
};

export const ImplementationPlanForm: StoryObj = {
  render: () => (
    <ImplementationPlanSection
      status="draft"
      ownerAssigned
      version={1}
      verificationMethodRequirement=""
      capabilities={FULL_CAPABILITIES}
      open
      onOpenChange={() => undefined}
      onPlan={() => undefined}
    />
  ),
};

/* ----------------------------------------------------------------------
 * ImplementationProgressSection — planned / in progress / complete
 * ---------------------------------------------------------------------- */

export const ImplementationProgressPlanned: StoryObj = {
  render: () => (
    <ImplementationProgressSection
      control={buildControl({
        status: "planned",
        implementation: {
          ...buildControl().implementation,
          actualStartDate: null,
          progress: 0,
        },
      })}
      capabilities={FULL_CAPABILITIES}
      startOpen={false}
      onStartOpenChange={() => undefined}
      progressOpen={false}
      onProgressOpenChange={() => undefined}
      completeOpen={false}
      onCompleteOpenChange={() => undefined}
      onStart={() => undefined}
      onProgress={() => undefined}
      onComplete={() => undefined}
    />
  ),
};

export const ImplementationProgressInProgress: StoryObj = {
  render: () => (
    <ImplementationProgressSection
      control={buildControl({ status: "in_implementation" })}
      capabilities={FULL_CAPABILITIES}
      startOpen={false}
      onStartOpenChange={() => undefined}
      progressOpen={false}
      onProgressOpenChange={() => undefined}
      completeOpen={false}
      onCompleteOpenChange={() => undefined}
      onStart={() => undefined}
      onProgress={() => undefined}
      onComplete={() => undefined}
    />
  ),
};

export const ImplementationProgressComplete: StoryObj = {
  render: () => (
    <ImplementationProgressSection
      control={buildControl({
        status: "implemented",
        implementation: {
          ...buildControl().implementation,
          actualCompletionDate: "2026-02-01T00:00:00Z",
          progress: 100,
        },
        evidence: sampleEvidence,
      })}
      capabilities={FULL_CAPABILITIES}
      startOpen={false}
      onStartOpenChange={() => undefined}
      progressOpen={false}
      onProgressOpenChange={() => undefined}
      completeOpen={false}
      onCompleteOpenChange={() => undefined}
      onStart={() => undefined}
      onProgress={() => undefined}
      onComplete={() => undefined}
    />
  ),
};

/* ----------------------------------------------------------------------
 * EvidenceList — empty / populated
 * ---------------------------------------------------------------------- */

export const EvidenceEmpty: StoryObj = {
  render: () => (
    <EvidenceList
      evidence={[]}
      status="in_implementation"
      version={4}
      capabilities={FULL_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onAdd={() => undefined}
    />
  ),
};

export const EvidencePopulated: StoryObj = {
  render: () => (
    <EvidenceList
      evidence={sampleEvidence}
      status="in_implementation"
      version={4}
      capabilities={FULL_CAPABILITIES}
      open={false}
      onOpenChange={() => undefined}
      onAdd={() => undefined}
    />
  ),
};

export const EvidenceAddForm: StoryObj = {
  render: () => (
    <EvidenceList
      evidence={sampleEvidence}
      status="in_implementation"
      version={4}
      capabilities={FULL_CAPABILITIES}
      open
      onOpenChange={() => undefined}
      onAdd={() => undefined}
    />
  ),
};

/* ----------------------------------------------------------------------
 * EffectivenessSummary — not verified / Effective / Partially Effective / Ineffective
 * ---------------------------------------------------------------------- */

export const EffectivenessNotVerified: StoryObj = {
  render: () => (
    <EffectivenessSummary
      latestResult={null}
      latestVerification={null}
      riskAssessmentId={RISK_ASSESSMENT_ID}
    />
  ),
};

export const EffectivenessEffective: StoryObj = {
  render: () => (
    <EffectivenessSummary
      latestResult="effective"
      latestVerification={buildVerification({ result: "effective" })}
      riskAssessmentId={RISK_ASSESSMENT_ID}
    />
  ),
};

export const EffectivenessPartiallyEffective: StoryObj = {
  render: () => (
    <EffectivenessSummary
      latestResult="partially_effective"
      latestVerification={buildVerification({
        result: "partially_effective",
        findings: "Guard shows minor wear; partial gap observed.",
      })}
      riskAssessmentId={RISK_ASSESSMENT_ID}
    />
  ),
};

export const EffectivenessIneffective: StoryObj = {
  render: () => (
    <EffectivenessSummary
      latestResult="ineffective"
      latestVerification={buildVerification({
        result: "ineffective",
        findings: "Guard was found removed during production changeover.",
      })}
      riskAssessmentId={RISK_ASSESSMENT_ID}
    />
  ),
};

/* ----------------------------------------------------------------------
 * VerificationHistory — empty / multi-record
 * ---------------------------------------------------------------------- */

export const VerificationHistoryEmpty: StoryObj = {
  render: () => <VerificationHistory verifications={[]} />,
};

export const VerificationHistoryMultiRecord: StoryObj = {
  render: () => (
    <VerificationHistory verifications={sampleVerificationHistory} />
  ),
};

/* ----------------------------------------------------------------------
 * VerificationForm
 * ---------------------------------------------------------------------- */

export const VerificationFormDefault: StoryObj = {
  render: () => (
    <VerificationForm
      status="implemented"
      capabilities={FULL_CAPABILITIES}
      reviewRequired={scheduledReviewSchedule.reviewRequired}
      noReviewReason={scheduledReviewSchedule.noReviewReason}
      hasExistingEvidence
      version={5}
      open
      onOpenChange={() => undefined}
      onSubmit={() => undefined}
    />
  ),
};

export const VerificationFormSubmitting: StoryObj = {
  render: () => (
    <VerificationForm
      status="implemented"
      capabilities={FULL_CAPABILITIES}
      reviewRequired={scheduledReviewSchedule.reviewRequired}
      noReviewReason={scheduledReviewSchedule.noReviewReason}
      hasExistingEvidence
      version={5}
      open
      onOpenChange={() => undefined}
      onSubmit={() => undefined}
      loading
    />
  ),
};

/* ----------------------------------------------------------------------
 * ReviewScheduleSection — scheduled / none / overdue
 * ---------------------------------------------------------------------- */

export const ReviewScheduled: StoryObj = {
  render: () => (
    <ReviewScheduleSection
      reviewSchedule={scheduledReviewSchedule}
      status="implemented"
      version={5}
      isOverdue={false}
      capabilities={FULL_CAPABILITIES}
      hasExistingEvidence
      scheduleOpen={false}
      onScheduleOpenChange={() => undefined}
      completeOpen={false}
      onCompleteOpenChange={() => undefined}
      onSchedule={() => undefined}
      onComplete={() => undefined}
    />
  ),
};

export const ReviewNone: StoryObj = {
  render: () => (
    <ReviewScheduleSection
      reviewSchedule={noReviewSchedule}
      status="implemented"
      version={5}
      isOverdue={false}
      capabilities={FULL_CAPABILITIES}
      hasExistingEvidence={false}
      scheduleOpen={false}
      onScheduleOpenChange={() => undefined}
      completeOpen={false}
      onCompleteOpenChange={() => undefined}
      onSchedule={() => undefined}
      onComplete={() => undefined}
    />
  ),
};

export const ReviewOverdue: StoryObj = {
  render: () => (
    <ReviewScheduleSection
      reviewSchedule={overdueReviewSchedule}
      status="implemented"
      version={5}
      isOverdue
      capabilities={FULL_CAPABILITIES}
      hasExistingEvidence
      scheduleOpen={false}
      onScheduleOpenChange={() => undefined}
      completeOpen={false}
      onCompleteOpenChange={() => undefined}
      onSchedule={() => undefined}
      onComplete={() => undefined}
    />
  ),
};

/* ----------------------------------------------------------------------
 * SourceSnapshot — present / absent
 * ---------------------------------------------------------------------- */

export const SourceSnapshotPresent: StoryObj = {
  render: () => <SourceSnapshot source={presentSource} />,
};

export const SourceSnapshotAbsent: StoryObj = {
  render: () => <SourceSnapshot source={absentSource} />,
};

/* ----------------------------------------------------------------------
 * RiskControlLifecycleActions —
 * draft / planned / implemented / suspended / archived / permission-limited
 * ---------------------------------------------------------------------- */

function noop() {
  // Story callbacks only need to exist — nothing observes their effects.
}

export const LifecycleDraft: StoryObj = {
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "draft", owner: sampleOwner })}
      capabilities={FULL_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};

export const LifecyclePlanned: StoryObj = {
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "planned" })}
      capabilities={FULL_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};

export const LifecycleImplemented: StoryObj = {
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "implemented" })}
      capabilities={FULL_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};

export const LifecycleSuspended: StoryObj = {
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "suspended" })}
      capabilities={FULL_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};

export const LifecycleArchived: StoryObj = {
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "archived" })}
      capabilities={FULL_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};

export const LifecyclePermissionLimited: StoryObj = {
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "implemented" })}
      capabilities={READ_ONLY_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};

export const LifecycleNarrowViewport: StoryObj = {
  parameters: {
    viewport: { defaultViewport: "mobile1" },
  },
  render: () => (
    <RiskControlLifecycleActions
      control={buildControl({ status: "implemented" })}
      capabilities={FULL_CAPABILITIES}
      onPlan={noop}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={() => true}
      onResume={() => true}
      onSupersede={() => true}
      onCancel={() => true}
      onArchive={() => true}
    />
  ),
};
