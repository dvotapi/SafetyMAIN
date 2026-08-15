import type { Meta, StoryObj } from "@storybook/react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Alert, Button, EmptyState, LoadingState } from "@/components";
import { RiskAssessmentActivity } from "@/features/risk-assessments/components/risk-assessment-activity";
import { RiskAssessmentConflictDialog } from "@/features/risk-assessments/components/risk-assessment-conflict-dialog";
import { RiskAssessmentForm } from "@/features/risk-assessments/components/risk-assessment-form";
import { RiskAssessmentLifecycleActions } from "@/features/risk-assessments/components/risk-assessment-lifecycle-actions";
import { RiskAssessmentRelatedControls } from "@/features/risk-assessments/components/risk-assessment-related-controls";
import {
  RiskAssessmentProperties,
  RiskAssessmentSummary,
} from "@/features/risk-assessments/components/risk-assessment-summary";
import { mapRiskAssessmentCapabilities } from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import {
  defaultRiskAssessmentFormValues,
  riskAssessmentFormSchema,
  type RiskAssessmentFormValues,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type {
  ControlMeasure,
  RelatedRiskControlSummary,
  RiskAssessment,
  RiskAssessmentHazardSummary,
} from "@/features/risk-assessments/types/risk-assessment-types";

const sampleHazardOptions: RiskAssessmentHazardSummary[] = [
  {
    id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
    code: "HZ-100",
    title: "Unguarded conveyor",
    status: "active",
  },
  {
    id: "dddddddd-dddd-dddd-dddd-dddddddddddd",
    code: "HZ-200",
    title: "Slippery floor",
    status: "active",
  },
];

const sampleProposedControl: ControlMeasure = {
  id: null,
  controlType: "engineering",
  description: "Install guard rail on conveyor",
  responsible: "Maintenance team",
  implemented: false,
  effective: null,
};

const sampleRelatedControl: RelatedRiskControlSummary = {
  id: "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  code: "RC-100",
  title: "Conveyor guard rail",
  hierarchyLevel: "engineering",
  lifecycleStatus: "active",
  ownerLabel: "Maintenance",
  latestEffectivenessResult: "effective",
  nextReviewDate: "2027-01-15",
};

const sampleRiskAssessment: RiskAssessment = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  organizationId: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
  code: "RA-100",
  title: "Conveyor belt risk assessment",
  assessmentProfile: "simple_5x5",
  assessedObject: {
    objectType: "equipment",
    reference: "CNV-12",
  },
  assessorId: "33333333-3333-3333-3333-333333333333",
  assessmentDate: "2026-07-25",
  reviewSchedule: {
    reviewDueDate: "2027-07-25",
    reviewFrequencyDays: 365,
    reviewReason: "Annual review",
    triggeredBy: "schedule",
  },
  inherentRisk: {
    level: "high",
    factors: [
      { factor: "probability", score: 4 },
      { factor: "severity", score: 5 },
    ],
    explanation: "Unguarded moving parts with high exposure.",
  },
  residualRisk: {
    level: "medium",
    factors: [
      { factor: "probability", score: 2 },
      { factor: "severity", score: 4 },
    ],
    explanation: "Residual risk after guard installation.",
  },
  controls: [sampleProposedControl],
  acceptance: {
    decision: "conditionally_accepted",
    justification: "Acceptable with guard and training.",
    reviewerId: "44444444-4444-4444-4444-444444444444",
    approvedAt: null,
  },
  competencyRequirements: ["Machine operator certification"],
  extensionReferences: {},
  status: "under_review",
  supersededById: null,
  archivedAt: null,
  archivedBy: null,
  approvedAt: null,
  approvedBy: null,
  createdAt: "2026-07-25T00:00:00Z",
  updatedAt: "2026-07-26T00:00:00Z",
  version: 2,
};

const sampleRelatedHazard = {
  id: sampleRiskAssessment.hazardId,
  code: "HZ-100",
  title: "Unguarded conveyor",
  status: "active",
};

const fullCapabilities = mapRiskAssessmentCapabilities(() => true);

const meta: Meta = {
  title: "Features/RiskAssessments",
};

export default meta;

export const RegistryEmpty: StoryObj = {
  render: () => (
    <EmptyState
      title="No risk assessments yet"
      description="Create the first risk assessment for this organization."
    />
  ),
};

export const RegistryLoading: StoryObj = {
  render: () => <LoadingState label="Loading risk assessments" />,
};

export const RegistryError: StoryObj = {
  render: () => (
    <Alert tone="danger" title="Unable to load risk assessments">
      The risk assessment registry could not be loaded. Try again later.
    </Alert>
  ),
};

function CreateFormStory() {
  const form = useForm<RiskAssessmentFormValues>({
    resolver: zodResolver(riskAssessmentFormSchema),
    defaultValues: defaultRiskAssessmentFormValues,
  });
  return (
    <RiskAssessmentForm
      form={form}
      onSubmit={() => undefined}
      hazardOptions={sampleHazardOptions}
    />
  );
}

export const CreateForm: StoryObj = {
  render: () => <CreateFormStory />,
};

export const ObjectSummary: StoryObj = {
  render: () => <RiskAssessmentSummary assessment={sampleRiskAssessment} />,
};

export const ObjectProperties: StoryObj = {
  render: () => (
    <RiskAssessmentProperties
      assessment={sampleRiskAssessment}
      relatedHazard={sampleRelatedHazard}
    />
  ),
};

export const LifecycleActions: StoryObj = {
  render: () => (
    <RiskAssessmentLifecycleActions
      assessment={sampleRiskAssessment}
      capabilities={fullCapabilities}
      onSubmitForReview={async () => true}
      onApprove={async () => true}
      onArchive={async () => true}
    />
  ),
};

export const RelatedControlsEmptyNoProposed: StoryObj = {
  render: () => (
    <RiskAssessmentRelatedControls
      proposedControls={[]}
      controls={[]}
      canView
    />
  ),
};

export const RelatedControlsNotMaterialized: StoryObj = {
  render: () => (
    <RiskAssessmentRelatedControls
      proposedControls={[sampleProposedControl]}
      controls={[]}
      canView
    />
  ),
};

export const RelatedControlsWithData: StoryObj = {
  render: () => (
    <RiskAssessmentRelatedControls
      proposedControls={[sampleProposedControl]}
      controls={[sampleRelatedControl]}
      canView
    />
  ),
};

export const ActivityUnavailable: StoryObj = {
  render: () => (
    <RiskAssessmentActivity items={[]} canView={false} loading={false} />
  ),
};

export const ActivityEmpty: StoryObj = {
  render: () => <RiskAssessmentActivity items={[]} canView loading={false} />,
};

export const PermissionDeniedCreate: StoryObj = {
  render: () => (
    <EmptyState
      title="Cannot create risk assessments"
      description="You do not have permission to create risk assessments."
      action={
        <Button asChild variant="secondary">
          <Link href="/safety/risk-assessments">Back to registry</Link>
        </Button>
      }
    />
  ),
};

export const ConflictDialog: StoryObj = {
  render: () => (
    <RiskAssessmentConflictDialog
      open
      onOpenChange={() => undefined}
      onReload={() => undefined}
    />
  ),
};
