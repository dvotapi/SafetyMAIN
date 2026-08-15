import { type ReactNode } from "react";

import { Heading, Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectHeaderProps {
  title: ReactNode;
  subtitle?: ReactNode;
  status?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function ObjectHeader({
  title,
  subtitle,
  status,
  meta,
  actions,
  className,
}: ObjectHeaderProps) {
  return (
    <header className={cx(styles.header, className)}>
      <div className={styles.headerMain}>
        <Heading level={1}>{title}</Heading>
        {subtitle ? (
          <Text tone="muted" variant="caption">
            {subtitle}
          </Text>
        ) : null}
        {status || meta ? (
          <div className={styles.headerMeta}>
            {status}
            {meta}
          </div>
        ) : null}
      </div>
      {actions ? <div className={styles.actions}>{actions}</div> : null}
    </header>
  );
}
