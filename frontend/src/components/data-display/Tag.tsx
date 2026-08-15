import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
}

export function Tag({ children, className, ...rest }: TagProps) {
  return (
    <span className={cx(styles.tag, className)} {...rest}>
      {children}
    </span>
  );
}
