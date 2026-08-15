import type { Meta, StoryObj } from "@storybook/react";

import { Select } from "@/components/primitives/Select";

const options = [
  { value: "draft", label: "Draft" },
  { value: "review", label: "In review" },
  { value: "published", label: "Published" },
];

const meta: Meta<typeof Select> = {
  title: "Primitives/Select",
  component: Select,
  args: {
    options,
    placeholder: "Choose status",
  },
};

export default meta;
type Story = StoryObj<typeof Select>;

export const Default: Story = {};

export const Disabled: Story = {
  args: { disabled: true, value: "draft" },
};

export const Error: Story = {
  args: { invalid: true, value: "review" },
};
