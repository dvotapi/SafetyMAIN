import type { Meta, StoryObj } from "@storybook/react";

import {
  StatusBadge,
  type VisualStatus,
} from "@/components/primitives/StatusBadge";

const statuses: VisualStatus[] = [
  "draft",
  "under_review",
  "approved",
  "rejected",
  "planned",
  "active",
  "implemented",
  "verified_effective",
  "verified_partially_effective",
  "verified_ineffective",
  "overdue",
  "superseded",
  "archived",
  "cancelled",
];

const meta: Meta<typeof StatusBadge> = {
  title: "Primitives/StatusBadge",
  component: StatusBadge,
};

export default meta;
type Story = StoryObj<typeof StatusBadge>;

export const Draft: Story = { args: { status: "draft" } };

export const Gallery: Story = {
  render: () => (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
      {statuses.map((status) => (
        <StatusBadge key={status} status={status} />
      ))}
    </div>
  ),
};
