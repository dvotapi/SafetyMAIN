import { type ReactNode } from "react";

import { Panel } from "@/components/primitives/Surface";
import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface ChartContainerProps {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function ChartContainer({
  title,
  actions,
  children,
  className,
}: ChartContainerProps) {
  return (
    <Panel
      heading={title}
      actions={actions}
      className={cx(styles.chartContainer, className)}
    >
      <div className={styles.chartBody}>{children}</div>
    </Panel>
  );
}
