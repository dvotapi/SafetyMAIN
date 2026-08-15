import type { Meta, StoryObj } from "@storybook/react";

import {
  NavigationItem,
  NavigationSection,
  SideNavigation,
} from "@/components/navigation";

const meta: Meta<typeof SideNavigation> = {
  title: "Navigation/SideNavigation",
  component: SideNavigation,
};

export default meta;
type Story = StoryObj<typeof SideNavigation>;

export const Default: Story = {
  render: () => (
    <SideNavigation>
      <NavigationSection title="Overview">
        <NavigationItem href="#" icon="home" active>
          Home
        </NavigationItem>
        <NavigationItem href="#" icon="layout-dashboard">
          Dashboard
        </NavigationItem>
      </NavigationSection>
      <NavigationSection title="Workspace">
        <NavigationItem href="#" icon="users">
          People
        </NavigationItem>
        <NavigationItem href="#" icon="settings">
          Settings
        </NavigationItem>
      </NavigationSection>
    </SideNavigation>
  ),
};
