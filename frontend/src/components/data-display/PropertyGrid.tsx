import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface PropertyGridProps extends HTMLAttributes<HTMLDivElement> {
  columns?: 2 | 3;
  children: ReactNode;
}

export function PropertyGrid({
  columns = 2,
  children,
  className,
  ...rest
}: PropertyGridProps) {
  return (
    <div
      className={cx(
        styles.grid,
        columns === 3 ? styles.gridCols3 : styles.gridCols2,
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
