"use client";

import * as TabsPrimitive from "@radix-ui/react-tabs";
import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Navigation.module.css";

export interface TabItem {
  value: string;
  label: ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  items: TabItem[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children?: ReactNode;
  className?: string;
  listClassName?: string;
}

export function Tabs({
  items,
  value,
  defaultValue,
  onValueChange,
  children,
  className,
  listClassName,
}: TabsProps) {
  const rootProps = {
    ...(value !== undefined ? { value } : {}),
    ...(defaultValue !== undefined ? { defaultValue } : {}),
    ...(onValueChange ? { onValueChange } : {}),
  };

  return (
    <TabsPrimitive.Root className={className} {...rootProps}>
      <TabsPrimitive.List className={cx(styles.tabsList, listClassName)}>
        {items.map((item) => (
          <TabsPrimitive.Trigger
            key={item.value}
            value={item.value}
            disabled={item.disabled}
            className={styles.tabTrigger}
          >
            {item.label}
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>
      {children}
    </TabsPrimitive.Root>
  );
}

export function TabPanel({
  value,
  children,
  className,
}: {
  value: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <TabsPrimitive.Content value={value} className={className}>
      {children}
    </TabsPrimitive.Content>
  );
}

export function SubTabs({
  items,
  value,
  defaultValue,
  onValueChange,
  className,
}: TabsProps) {
  const rootProps = {
    ...(value !== undefined ? { value } : {}),
    ...(defaultValue !== undefined ? { defaultValue } : {}),
    ...(onValueChange ? { onValueChange } : {}),
  };

  return (
    <TabsPrimitive.Root className={className} {...rootProps}>
      <TabsPrimitive.List className={styles.subTabsList}>
        {items.map((item) => (
          <TabsPrimitive.Trigger
            key={item.value}
            value={item.value}
            disabled={item.disabled}
            className={styles.subTabTrigger}
          >
            {item.label}
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>
    </TabsPrimitive.Root>
  );
}
