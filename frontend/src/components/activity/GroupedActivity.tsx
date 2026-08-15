import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Activity.module.css";

export interface GroupedActivityProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export function GroupedActivity({
  label,
  children,
  className,
}: GroupedActivityProps) {
  return (
    <section className={cx(styles.group, className)}>
      <div className={styles.groupLabel}>{label}</div>
      {children}
    </section>
  );
}
