"use client";

import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface FilterChipProps {
  label: string;
  value: string;
  onRemove?: () => void;
  removeLabel?: string;
  className?: string;
}

export function FilterChip({
  label,
  value,
  onRemove,
  removeLabel = "Удалить фильтр",
  className,
}: FilterChipProps) {
  return (
    <span className={cx(styles.filterChip, className)}>
      <span className={styles.filterChipLabel}>{label}:</span>
      <span className={styles.filterChipValue}>{value}</span>
      {onRemove ? (
        <button
          type="button"
          aria-label={removeLabel}
          onClick={onRemove}
          style={{
            border: 0,
            background: "transparent",
            padding: 0,
            cursor: "pointer",
            display: "inline-flex",
          }}
        >
          <Icon name="x" size="xs" decorative />
        </button>
      ) : null}
    </span>
  );
}
