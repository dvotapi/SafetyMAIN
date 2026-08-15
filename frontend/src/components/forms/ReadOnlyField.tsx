import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Forms.module.css";

export interface ReadOnlyFieldProps {
  label: ReactNode;
  value: ReactNode;
  className?: string;
}

export function ReadOnlyField({ label, value, className }: ReadOnlyFieldProps) {
  return (
    <div className={cx(styles.readOnlyField, className)}>
      <div className={styles.readOnlyLabel}>{label}</div>
      <div className={styles.readOnlyValue}>{value}</div>
    </div>
  );
}
