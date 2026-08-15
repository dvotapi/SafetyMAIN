import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Forms.module.css";

export interface FormRowProps extends HTMLAttributes<HTMLDivElement> {
  columns?: 1 | 2;
  children: ReactNode;
}

export function FormRow({
  columns = 1,
  children,
  className,
  ...rest
}: FormRowProps) {
  return (
    <div
      className={cx(
        styles.formRow,
        columns === 2 && styles.formRowCols2,
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
