import type { Meta, StoryObj } from "@storybook/react";

import { Alert } from "@/components/feedback/Feedback";
import { Badge } from "@/components/primitives/StatusBadge";
import { Card, Panel } from "@/components/primitives/Surface";
import { Heading, Text } from "@/components/primitives/Text";
import { Spinner, Skeleton } from "@/components/feedback/Feedback";

const meta: Meta = {
  title: "Primitives/SurfacesAndFeedback",
};

export default meta;

export const Cards: StoryObj = {
  render: () => (
    <div style={{ display: "grid", gap: 16 }}>
      <Card>
        <Heading level={3}>Card</Heading>
        <Text>Surface using semantic tokens.</Text>
        <Badge>12</Badge>
      </Card>
      <Panel heading={<Heading level={3}>Panel</Heading>}>
        <Alert tone="info">Informational alert</Alert>
        <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
          <Spinner />
          <Skeleton width="160px" height="24px" />
        </div>
      </Panel>
    </div>
  ),
};
