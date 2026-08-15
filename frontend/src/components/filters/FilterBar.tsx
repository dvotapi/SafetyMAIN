import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface FilterBarProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function FilterBar({ children, className, ...rest }: FilterBarProps) {
  return (
    <div className={cx(styles.bar, className)} role="search" {...rest}>
      {children}
    </div>
  );
}
