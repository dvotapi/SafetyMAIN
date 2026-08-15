import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export interface RegistryActionsProps {
  children: ReactNode;
  className?: string;
}

export function RegistryActions({ children, className }: RegistryActionsProps) {
  return <div className={cx(styles.toolbarSection, className)}>{children}</div>;
}
