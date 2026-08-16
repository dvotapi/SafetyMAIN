"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { type ReactNode } from "react";

import { Avatar } from "@/components/data-display/Avatar";
import { Button } from "@/components/primitives/Button";
import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Navigation.module.css";

export interface OverflowMenuItem {
  id: string;
  label: ReactNode;
  icon?: ReactNode;
  destructive?: boolean;
  disabled?: boolean;
  onSelect?: () => void;
}

export function OverflowMenu({
  items,
  label = "Другие действия",
  className,
}: {
  items: OverflowMenuItem[];
  label?: string;
  className?: string;
}) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={className}
          aria-label={label}
        >
          <Icon name="more-horizontal" size="sm" decorative />
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content className={styles.menuContent} sideOffset={4}>
          {items.map((item) => (
            <DropdownMenu.Item
              key={item.id}
              {...(item.disabled ? { disabled: true } : {})}
              className={cx(
                styles.menuItem,
                item.destructive && styles.menuItemDanger,
              )}
              {...(item.onSelect ? { onSelect: item.onSelect } : {})}
            >
              {item.icon}
              {item.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

export interface UserMenuItem {
  id: string;
  label: ReactNode;
  destructive?: boolean;
  disabled?: boolean;
  onSelect?: () => void;
}

export function UserMenu({
  name,
  items,
  className,
}: {
  name: string;
  items: UserMenuItem[];
  className?: string;
}) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          variant="secondary"
          size="sm"
          className={cx(styles.userMenuTrigger, className)}
        >
          <Avatar name={name} size="sm" />
          {name}
          <Icon name="chevron-down" size="sm" decorative />
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content className={styles.menuContent} align="end">
          {items.map((item) => (
            <DropdownMenu.Item
              key={item.id}
              {...(item.disabled ? { disabled: true } : {})}
              className={cx(
                styles.menuItem,
                item.destructive && styles.menuItemDanger,
              )}
              {...(item.onSelect ? { onSelect: item.onSelect } : {})}
            >
              {item.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

export function OrganizationSwitcher({
  organizationName,
  className,
  onClick,
}: {
  organizationName: string;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <Button
      variant="secondary"
      size="sm"
      className={cx(styles.orgButton, className)}
      onClick={onClick}
    >
      <Icon name="building-2" size="sm" decorative />
      <span className={styles.orgLabel}>{organizationName}</span>
      <Icon name="chevron-down" size="sm" decorative />
    </Button>
  );
}
