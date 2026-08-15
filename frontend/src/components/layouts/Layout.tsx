import { type HTMLAttributes, type ReactNode } from "react";

import { Card, Divider, Panel } from "@/components/primitives/Surface";
import { cx } from "@/utils/cx";

import styles from "./Layout.module.css";

export { Card, Divider, Panel };

export type ContainerWidth = "default" | "wide" | "narrow";

export function Container({
  width = "default",
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  width?: ContainerWidth;
}) {
  return (
    <div
      className={cx(
        styles.container,
        width === "wide" && styles.containerWide,
        width === "narrow" && styles.containerNarrow,
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export type StackGap = 1 | 2 | 3 | 4 | 6 | 8;

export function Stack({
  gap = 4,
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  gap?: StackGap;
}) {
  return (
    <div className={cx(styles.stack, styles[`gap${gap}`], className)} {...rest}>
      {children}
    </div>
  );
}

export function Inline({
  gap = 2,
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  gap?: StackGap;
}) {
  return (
    <div
      className={cx(styles.inline, styles[`gap${gap}`], className)}
      {...rest}
    >
      {children}
    </div>
  );
}

export type GridCols = 1 | 2 | 3 | 4;

export function Grid({
  cols = 2,
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  cols?: GridCols;
}) {
  return (
    <div
      className={cx(styles.grid, styles[`cols${cols}`], className)}
      {...rest}
    >
      {children}
    </div>
  );
}

export function Section({
  title,
  description,
  actions,
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLElement> & {
  children: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className={cx(styles.section, className)} {...rest}>
      {title || description || actions ? (
        <div className={styles.sectionHeader}>
          <div>
            {title}
            {description}
          </div>
          {actions}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function Spacer({
  size = 4,
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { size?: StackGap }) {
  return (
    <div
      aria-hidden
      className={cx(styles.spacer, className)}
      style={{ height: `var(--sm-space-${size})` }}
      {...rest}
    />
  );
}

export function SplitView({
  primary,
  secondary,
  reverse,
  className,
}: {
  primary: ReactNode;
  secondary: ReactNode;
  reverse?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cx(styles.split, reverse && styles.splitReverse, className)}
    >
      <div>{primary}</div>
      <aside>{secondary}</aside>
    </div>
  );
}

export function ResizablePanel({
  primary,
  secondary,
  className,
}: {
  primary: ReactNode;
  secondary: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.resizable, className)}>
      <div className={cx(styles.panel, styles.primaryPanel)}>{primary}</div>
      <div className={cx(styles.panel, styles.secondaryPanel)}>{secondary}</div>
    </div>
  );
}
