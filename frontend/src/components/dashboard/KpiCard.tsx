import { type ReactNode } from "react";

import { Card } from "@/components/primitives/Surface";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface KpiCardProps {
  label: ReactNode;
  value: ReactNode;
  delta?: ReactNode;
  className?: string;
}

export function KpiCard({ label, value, delta, className }: KpiCardProps) {
  return (
    <Card className={cx(styles.kpi, className)}>
      <Text variant="label" tone="muted">
        {label}
      </Text>
      <Text as="div" variant="body">
        <strong>{value}</strong>
      </Text>
      {delta ? (
        <Text variant="caption" tone="muted">
          {delta}
        </Text>
      ) : null}
    </Card>
  );
}
