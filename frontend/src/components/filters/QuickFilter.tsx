"use client";

import { type ButtonHTMLAttributes } from "react";

import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface QuickFilterProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  count?: number;
}

export function QuickFilter({
  active = false,
  count,
  children,
  className,
  type = "button",
  ...rest
}: QuickFilterProps) {
  return (
    <button
      type={type}
      className={cx(
        styles.quickFilter,
        active && styles.quickFilterActive,
        className,
      )}
      aria-pressed={active}
      {...rest}
    >
      {children}
      {count !== undefined ? ` (${count})` : null}
    </button>
  );
}
