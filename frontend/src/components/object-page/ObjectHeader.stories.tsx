import type { Meta, StoryObj } from "@storybook/react";

import { Button } from "@/components/primitives/Button";
import { StatusBadge } from "@/components/primitives/StatusBadge";
import { ObjectHeader } from "@/components/object-page/ObjectHeader";

const meta: Meta<typeof ObjectHeader> = {
  title: "Object Page/ObjectHeader",
  component: ObjectHeader,
};

export default meta;
type Story = StoryObj<typeof ObjectHeader>;

export const Default: Story = {
  args: {
    title: "HAZ-1042 — Slip hazard near loading dock",
    subtitle: "Last updated 2 hours ago · Version 3",
    status: <StatusBadge status="under_review" />,
    meta: <span>Owner: Alex Morgan</span>,
    actions: (
      <>
        <Button variant="secondary" size="sm">
          Edit
        </Button>
        <Button size="sm">Submit for review</Button>
      </>
    ),
  },
};
