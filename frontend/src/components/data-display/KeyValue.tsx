import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface KeyValueProps extends HTMLAttributes<HTMLDivElement> {
  label: ReactNode;
  value: ReactNode;
}

export function KeyValue({ label, value, className, ...rest }: KeyValueProps) {
  return (
    <div className={cx(styles.keyValue, className)} {...rest}>
      <span className={styles.keyValueLabel}>{label}</span>
      <span className={styles.keyValueValue}>{value}</span>
    </div>
  );
}
