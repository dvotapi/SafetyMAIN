import type { Meta, StoryObj } from "@storybook/react";

import { WorkflowStepper } from "@/components/workflow/WorkflowStepper";

const steps = [
  { id: "draft", label: "Draft" },
  { id: "review", label: "Review" },
  { id: "approve", label: "Approve" },
  { id: "implement", label: "Implement" },
];

const meta: Meta<typeof WorkflowStepper> = {
  title: "Workflow/WorkflowStepper",
  component: WorkflowStepper,
};

export default meta;
type Story = StoryObj<typeof WorkflowStepper>;

export const InProgress: Story = {
  args: {
    steps,
    currentStepId: "review",
    completedStepIds: ["draft"],
  },
};

export const Complete: Story = {
  args: {
    steps,
    currentStepId: "implement",
    completedStepIds: ["draft", "review", "approve"],
  },
};
