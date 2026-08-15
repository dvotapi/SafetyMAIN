import { type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectActionsProps {
  children: ReactNode;
  className?: string;
}

export function ObjectActions({ children, className }: ObjectActionsProps) {
  return <div className={cx(styles.actions, className)}>{children}</div>;
}
