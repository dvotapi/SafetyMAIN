"use client";

import { type HTMLAttributes, type ReactNode } from "react";

import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface ChipProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  onRemove?: () => void;
  removeLabel?: string;
}

export function Chip({
  children,
  onRemove,
  removeLabel = "Remove",
  className,
  ...rest
}: ChipProps) {
  return (
    <span className={cx(styles.chip, className)} {...rest}>
      {children}
      {onRemove ? (
        <button
          type="button"
          className={styles.chipRemove}
          aria-label={removeLabel}
          onClick={onRemove}
        >
          <Icon name="x" size="xs" decorative />
        </button>
      ) : null}
    </span>
  );
}
