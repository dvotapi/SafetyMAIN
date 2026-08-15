import type { Meta, StoryObj } from "@storybook/react";

import {
  Alert,
  Avatar,
  Badge,
  Banner,
  Button,
  Card,
  Checkbox,
  Chip,
  EmptyState,
  Inline,
  Input,
  KpiCard,
  Label,
  Panel,
  ProgressBar,
  Select,
  Stack,
  StatusBadge,
  Switch,
  Tag,
  Text,
  WorkflowStepper,
} from "@/components";

const meta: Meta = {
  title: "Catalog/Gallery",
  parameters: { layout: "padded" },
};

export default meta;
type Story = StoryObj;

export const PrimitivesAndPatterns: Story = {
  render: () => (
    <Stack gap={6}>
      <section>
        <Text variant="label">Actions & inputs</Text>
        <Stack gap={3} style={{ marginTop: 8 }}>
          <Inline gap={2}>
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="danger" loading>
              Loading
            </Button>
          </Inline>
          <Label htmlFor="gal-input" required>
            Title
          </Label>
          <Input id="gal-input" placeholder="Sample" />
          <Select
            aria-label="Sample select"
            options={[
              { value: "a", label: "Option A" },
              { value: "b", label: "Option B" },
            ]}
            placeholder="Choose"
          />
          <Inline gap={3}>
            <Checkbox label="Accept" />
            <Inline gap={2}>
              <Switch id="gal-switch" aria-label="Enabled" />
              <Text as="span" variant="label">
                Enabled
              </Text>
            </Inline>
          </Inline>
        </Stack>
      </section>
      <section>
        <Text variant="label">Status & feedback</Text>
        <Inline gap={2} style={{ marginTop: 8, flexWrap: "wrap" }}>
          <StatusBadge status="draft" />
          <StatusBadge status="verified_effective" />
          <StatusBadge status="overdue" />
          <Badge>12</Badge>
          <Chip>Filter</Chip>
          <Tag>Tag</Tag>
          <Avatar name="Ada Lovelace" />
        </Inline>
        <div style={{ marginTop: 12 }}>
          <Alert tone="info">Informational alert</Alert>
        </div>
        <div style={{ marginTop: 8 }}>
          <Banner tone="warning">Review required</Banner>
        </div>
        <div style={{ marginTop: 8 }}>
          <ProgressBar value={64} label="Progress" />
        </div>
        <div style={{ marginTop: 8 }}>
          <EmptyState title="No items" description="Create the first record." />
        </div>
      </section>
      <section>
        <Text variant="label">Surfaces & workflow</Text>
        <Stack gap={3} style={{ marginTop: 8 }}>
          <Card>
            <KpiCard label="Open items" value="24" />
          </Card>
          <Panel heading={<Text variant="label">Panel</Text>}>
            <WorkflowStepper
              currentStepId="2"
              completedStepIds={["1"]}
              steps={[
                { id: "1", label: "Identify" },
                { id: "2", label: "Assess" },
                { id: "3", label: "Control" },
              ]}
            />
          </Panel>
        </Stack>
      </section>
    </Stack>
  ),
};
