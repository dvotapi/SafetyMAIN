import type { Meta, StoryObj } from "@storybook/react";

import { Alert } from "@/components/feedback/Feedback";
import { UserMenu } from "@/components/navigation/Menus";
import { Heading, Text } from "@/components/primitives/Text";

const meta: Meta = {
  title: "Auth/ShellStates",
};

export default meta;

export const UserMenuDefault: StoryObj = {
  render: () => (
    <UserMenu
      name="Ada Lovelace"
      items={[
        { id: "email", label: "ada@example.com", disabled: true },
        { id: "logout", label: "Sign out", destructive: true },
      ]}
    />
  ),
};

export const Unauthorized: StoryObj = {
  render: () => (
    <div style={{ maxWidth: 480 }}>
      <Heading level={1}>Authentication required</Heading>
      <Alert tone="warning" title="401 Unauthorized">
        You need to sign in to continue.
      </Alert>
    </div>
  ),
};

export const Forbidden: StoryObj = {
  render: () => (
    <div style={{ maxWidth: 480 }}>
      <Heading level={1}>Access denied</Heading>
      <Alert tone="danger" title="403 Forbidden">
        You do not have permission to view this area.
      </Alert>
    </div>
  ),
};

export const SessionExpired: StoryObj = {
  render: () => (
    <div style={{ maxWidth: 480 }}>
      <Heading level={1}>Session expired</Heading>
      <Alert tone="warning" title="Please sign in again">
        Your session ended or the refresh token is no longer valid.
      </Alert>
      <Text tone="secondary">Return to sign in to continue.</Text>
    </div>
  ),
};

export const AuthLoading: StoryObj = {
  render: () => <Text tone="secondary">Restoring session…</Text>,
};
