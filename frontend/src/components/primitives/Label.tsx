import { type LabelHTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Field.module.css";

export function RequiredIndicator() {
  return (
    <span className={styles.required} aria-hidden>
      *
    </span>
  );
}

export interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
  children: ReactNode;
}

export function Label({ required, children, className, ...rest }: LabelProps) {
  return (
    <label className={cx(styles.label, className)} {...rest}>
      {children}
      {required ? <RequiredIndicator /> : null}
    </label>
  );
}

export function HelperText({
  id,
  children,
  className,
}: {
  id?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <p id={id} className={cx(styles.hint, className)}>
      {children}
    </p>
  );
}

export function FieldError({
  id,
  children,
  className,
}: {
  id?: string;
  children: ReactNode;
  className?: string;
}) {
  if (!children) {
    return null;
  }
  return (
    <p id={id} className={cx(styles.error, className)} role="alert">
      {children}
    </p>
  );
}
