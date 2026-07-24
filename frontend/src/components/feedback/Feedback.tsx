import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Feedback.module.css";

export function Spinner({
  className,
  label = "Loading",
  ...rest
}: HTMLAttributes<HTMLDivElement> & { label?: string }) {
  return (
    <div
      className={cx(styles.spinner, className)}
      role="status"
      aria-label={label}
      {...rest}
    />
  );
}

export function Skeleton({
  className,
  width,
  height,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { width?: string; height?: string }) {
  return (
    <div
      className={cx(styles.skeleton, className)}
      style={{ width, height }}
      aria-hidden
      {...rest}
    />
  );
}

export type AlertTone = "info" | "success" | "warning" | "danger";

export function Alert({
  tone = "info",
  title,
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  tone?: AlertTone;
  title?: string;
  children: ReactNode;
}) {
  return (
    <div
      role="alert"
      className={cx(styles.alert, styles[tone], className)}
      {...rest}
    >
      <div>
        {title ? <strong>{title}</strong> : null}
        <div>{children}</div>
      </div>
    </div>
  );
}
