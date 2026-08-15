import { type ReactNode } from "react";

import { Heading, Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Navigation.module.css";

export function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  breadcrumbs?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cx(styles.pageHeader, className)}>
      <div className={styles.pageHeaderMain}>
        {breadcrumbs}
        <Heading level={1}>{title}</Heading>
        {description ? (
          typeof description === "string" ? (
            <Text tone="secondary">{description}</Text>
          ) : (
            description
          )
        ) : null}
      </div>
      {actions}
    </header>
  );
}

export function CommandBar({
  start,
  end,
  className,
}: {
  start?: ReactNode;
  end?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.commandBar, className)}>
      <div className={styles.commandStart}>{start}</div>
      <div className={styles.commandEnd}>{end}</div>
    </div>
  );
}
