"use client";

import { DatePicker } from "@/components/primitives/Input";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface DateRangeFilterProps {
  from?: string;
  to?: string;
  onFromChange?: (value: string) => void;
  onToChange?: (value: string) => void;
  fromLabel?: string;
  toLabel?: string;
  className?: string;
}

export function DateRangeFilter({
  from,
  to,
  onFromChange,
  onToChange,
  fromLabel = "С",
  toLabel = "По",
  className,
}: DateRangeFilterProps) {
  return (
    <div className={cx(styles.dateRange, className)}>
      <label>
        <Text as="span" variant="caption" tone="muted">
          {fromLabel}
        </Text>
        <DatePicker
          value={from ?? ""}
          onChange={(event) => onFromChange?.(event.target.value)}
        />
      </label>
      <span className={styles.dateRangeSep} aria-hidden>
        —
      </span>
      <label>
        <Text as="span" variant="caption" tone="muted">
          {toLabel}
        </Text>
        <DatePicker
          value={to ?? ""}
          onChange={(event) => onToChange?.(event.target.value)}
        />
      </label>
    </div>
  );
}
