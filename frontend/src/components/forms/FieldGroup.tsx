import { type FieldsetHTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Forms.module.css";

export interface FieldGroupProps extends FieldsetHTMLAttributes<HTMLFieldSetElement> {
  legend?: ReactNode;
  children: ReactNode;
}

export function FieldGroup({
  legend,
  children,
  className,
  ...rest
}: FieldGroupProps) {
  return (
    <fieldset className={cx(styles.fieldGroup, className)} {...rest}>
      {legend ? (
        <legend className={styles.fieldGroupLegend}>{legend}</legend>
      ) : null}
      {children}
    </fieldset>
  );
}
