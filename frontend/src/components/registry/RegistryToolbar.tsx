import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export interface RegistryToolbarProps {
  filters?: ReactNode;
  search?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function RegistryToolbar({
  filters,
  search,
  actions,
  className,
}: RegistryToolbarProps) {
  return (
    <div className={cx(styles.toolbar, className)}>
      <div className={styles.toolbarSection}>
        {search}
        {filters}
      </div>
      {actions ? <div className={styles.toolbarSection}>{actions}</div> : null}
    </div>
  );
}
