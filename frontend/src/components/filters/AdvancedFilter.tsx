"use client";

import { useState, type ReactNode } from "react";

import { Button } from "@/components/primitives/Button";
import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface AdvancedFilterProps {
  label?: string;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function AdvancedFilter({
  label = "Advanced filters",
  children,
  defaultOpen = false,
  className,
}: AdvancedFilterProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={className}>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className={styles.advancedToggle}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <Icon name="sliders-horizontal" size="sm" decorative />
        {label}
        <Icon
          name={open ? "chevron-up" : "chevron-down"}
          size="sm"
          decorative
        />
      </Button>
      {open ? <div className={cx(styles.advancedPanel)}>{children}</div> : null}
    </div>
  );
}
