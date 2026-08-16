"use client";

import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectTab {
  id: string;
  label: string;
}

export interface ObjectTabsProps {
  tabs: ObjectTab[];
  activeTabId: string;
  onTabChange?: (tabId: string) => void;
  className?: string;
}

export function ObjectTabs({
  tabs,
  activeTabId,
  onTabChange,
  className,
}: ObjectTabsProps) {
  return (
    <div
      className={cx(styles.tabs, className)}
      role="tablist"
      aria-label="Разделы объекта"
    >
      {tabs.map((tab) => {
        const active = tab.id === activeTabId;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            className={cx(styles.tab, active && styles.tabActive)}
            aria-selected={active}
            onClick={() => onTabChange?.(tab.id)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
