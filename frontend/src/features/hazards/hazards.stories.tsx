import type { Meta, StoryObj } from "@storybook/react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { HazardForm } from "@/features/hazards/components/hazard-form";
import { HazardLifecycleActions } from "@/features/hazards/components/hazard-lifecycle-actions";
import {
  HazardRelatedAssessments,
  HazardRiskSummary,
} from "@/features/hazards/components/hazard-related-assessments";
import {
  HazardProperties,
  HazardSummary,
} from "@/features/hazards/components/hazard-summary";
import { mapHazardCapabilities } from "@/features/hazards/hooks/use-hazard-permissions";
import {
  defaultHazardFormValues,
  hazardFormSchema,
  type HazardFormValues,
} from "@/features/hazards/schemas/hazard-form-schema";
import type { Hazard } from "@/features/hazards/types/hazard-types";

const sampleHazard: Hazard = {
  id: "11111111-1111-1111-1111-111111111111",
  organizationId: "22222222-2222-2222-2222-222222222222",
  code: "HZ-100",
  title: "Unguarded conveyor",
  description: "Missing guard on conveyor belt",
  category: "mechanical",
  safetyDirections: ["occupational_safety"],
  source: "inspection",
  affectedSubjects: ["employee"],
  locationReference: "Bay 3",
  processReference: null,
  equipmentReference: "CNV-12",
  extensionReferences: {},
  status: "draft",
  identifiedAt: "2026-07-25T00:00:00Z",
  identifiedBy: "33333333-3333-3333-3333-333333333333",
  reviewedAt: null,
  reviewedBy: null,
  archivedAt: null,
  archivedBy: null,
  createdAt: "2026-07-25T00:00:00Z",
  updatedAt: "2026-07-25T00:00:00Z",
  version: 1,
};

const meta: Meta = {
  title: "Features/Hazards",
};

export default meta;

export const Summary: StoryObj = {
  render: () => <HazardSummary hazard={sampleHazard} />,
};

export const Properties: StoryObj = {
  render: () => <HazardProperties hazard={sampleHazard} />,
};

export const LifecycleActions: StoryObj = {
  render: () => (
    <HazardLifecycleActions
      hazard={sampleHazard}
      capabilities={mapHazardCapabilities(() => true)}
      onActivate={async () => undefined}
      onArchive={async () => undefined}
      onRestore={async () => undefined}
    />
  ),
};

export const RiskSummary: StoryObj = {
  render: () => (
    <HazardRiskSummary
      assessments={[
        {
          id: "ra-1",
          code: "RA-1",
          title: "Conveyor assessment",
          status: "approved",
          assessmentProfile: "general",
          inherentRiskLabel: "High",
          residualRiskLabel: "Medium",
          approvedAt: "2026-07-20T00:00:00Z",
          updatedAt: "2026-07-20T00:00:00Z",
        },
      ]}
    />
  ),
};

export const RelatedAssessmentsEmpty: StoryObj = {
  render: () => (
    <HazardRelatedAssessments assessments={[]} canView loading={false} />
  ),
};

function FormStory() {
  const form = useForm<HazardFormValues>({
    resolver: zodResolver(hazardFormSchema),
    defaultValues: defaultHazardFormValues,
  });
  return <HazardForm form={form} onSubmit={() => undefined} />;
}

export const FormDefault: StoryObj = {
  render: () => <FormStory />,
};
