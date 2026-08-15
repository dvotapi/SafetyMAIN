import { type ReactNode } from "react";

import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Registry.module.css";

export interface RegistryPaginationProps {
  children?: ReactNode;
  summary?: ReactNode;
  className?: string;
}

export function RegistryPagination({
  children,
  summary,
  className,
}: RegistryPaginationProps) {
  return (
    <div className={cx(styles.toolbarSection, className)}>
      {summary ? (
        <Text variant="caption" tone="muted">
          {summary}
        </Text>
      ) : null}
      {children}
    </div>
  );
}
