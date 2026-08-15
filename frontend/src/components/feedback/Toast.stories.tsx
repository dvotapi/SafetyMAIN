import type { Meta, StoryObj } from "@storybook/react";

import { Button } from "@/components/primitives/Button";
import { ToastProvider, useToast } from "@/components/feedback/Toast";

function ToastDemo() {
  const { toast } = useToast();
  return (
    <Button
      variant="secondary"
      onClick={() =>
        toast({
          title: "Changes saved",
          description: "Your updates were applied successfully.",
          tone: "success",
        })
      }
    >
      Show toast
    </Button>
  );
}

function ToastStoryWrapper() {
  return (
    <ToastProvider>
      <ToastDemo />
    </ToastProvider>
  );
}

const meta: Meta<typeof ToastStoryWrapper> = {
  title: "Feedback/Toast",
  component: ToastStoryWrapper,
};

export default meta;
type Story = StoryObj<typeof ToastStoryWrapper>;

export const Default: Story = {};
