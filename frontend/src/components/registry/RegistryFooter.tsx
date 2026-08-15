import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export interface RegistryFooterProps {
  pagination?: ReactNode;
  selection?: ReactNode;
  className?: string;
}

export function RegistryFooter({
  pagination,
  selection,
  className,
}: RegistryFooterProps) {
  return (
    <div className={cx(styles.footer, className)}>
      {selection}
      {pagination}
    </div>
  );
}
