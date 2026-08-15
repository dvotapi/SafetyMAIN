import { type ReactNode } from "react";

import { Panel } from "@/components/primitives/Surface";
import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectSummaryProps {
  children: ReactNode;
  heading?: ReactNode;
  className?: string;
}

export function ObjectSummary({
  children,
  heading = "Summary",
  className,
}: ObjectSummaryProps) {
  return (
    <Panel heading={heading} className={cx(styles.summary, className)}>
      {children}
    </Panel>
  );
}
