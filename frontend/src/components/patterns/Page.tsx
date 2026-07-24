import { type HTMLAttributes, type ReactNode } from "react";

import { Heading } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Page.module.css";

export function PageContainer({
  children,
  variant = "default",
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  variant?: "default" | "object";
}) {
  return (
    <div
      className={cx(
        styles.container,
        variant === "object" && styles.object,
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cx(styles.header, className)}>
      <div>
        <Heading level={1}>{title}</Heading>
        {description}
      </div>
      {actions}
    </header>
  );
}

export function PageSection({
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLElement> & { children: ReactNode }) {
  return (
    <section className={cx(styles.section, className)} {...rest}>
      {children}
    </section>
  );
}

export function PageActions({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cx(styles.actions, className)}>{children}</div>;
}

export function ContentGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cx(styles.grid, className)}>{children}</div>;
}

export function SplitLayout({
  primary,
  secondary,
  className,
}: {
  primary: ReactNode;
  secondary: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.split, className)}>
      <div>{primary}</div>
      <aside>{secondary}</aside>
    </div>
  );
}
