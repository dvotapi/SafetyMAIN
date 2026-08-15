import type { Meta, StoryObj } from "@storybook/react";

import { Timeline } from "@/components/timeline/Timeline";

const meta: Meta<typeof Timeline> = {
  title: "Timeline/Timeline",
  component: Timeline,
};

export default meta;
type Story = StoryObj<typeof Timeline>;

export const Default: Story = {
  args: {
    events: [
      {
        id: "1",
        title: "Hazard created",
        description: "Initial record submitted",
        timestamp: new Date(Date.now() - 1000 * 60 * 30),
        icon: "file-pen",
      },
      {
        id: "2",
        title: "Review started",
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
        icon: "eye",
      },
      {
        id: "3",
        title: "Approved",
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 26),
        icon: "circle-check",
      },
    ],
  },
};

export const CollapsedGroup: Story = {
  args: {
    events: [
      {
        id: "a",
        title: "Morning event",
        timestamp: "2026-07-24T09:00:00",
      },
      {
        id: "b",
        title: "Earlier event",
        timestamp: "2026-07-23T14:00:00",
      },
    ],
    defaultExpandedGroups: { "July 23, 2026": false },
  },
};
