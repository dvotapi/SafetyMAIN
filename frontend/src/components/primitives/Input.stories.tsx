import type { Meta, StoryObj } from "@storybook/react";

import { Input } from "@/components/primitives/Input";
import { Label } from "@/components/primitives/Label";

const meta: Meta<typeof Input> = {
  title: "Primitives/Input",
  component: Input,
  args: {
    placeholder: "Enter value",
  },
};

export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = {
  render: (args) => (
    <Label htmlFor="input-default">
      Label
      <Input id="input-default" {...args} />
    </Label>
  ),
};

export const Disabled: Story = {
  args: { disabled: true, value: "Disabled value" },
  render: (args) => (
    <Label htmlFor="input-disabled">
      Label
      <Input id="input-disabled" {...args} />
    </Label>
  ),
};

export const Error: Story = {
  args: { invalid: true, defaultValue: "Invalid value" },
  render: (args) => (
    <Label htmlFor="input-error">
      Label
      <Input id="input-error" {...args} />
    </Label>
  ),
};
