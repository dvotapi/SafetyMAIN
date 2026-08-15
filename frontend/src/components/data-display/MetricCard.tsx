import { type HTMLAttributes, type ReactNode } from "react";

import { Card } from "@/components/primitives/Surface";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface MetricCardProps extends HTMLAttributes<HTMLDivElement> {
  label: ReactNode;
  value: ReactNode;
  hint?: ReactNode;
  accessory?: ReactNode;
}

export function MetricCard({
  label,
  value,
  hint,
  accessory,
  className,
  ...rest
}: MetricCardProps) {
  return (
    <Card className={cx(styles.metricCard, className)} {...rest}>
      <div className={styles.metricHeader}>
        <Text as="span" variant="label" tone="muted">
          {label}
        </Text>
        {accessory}
      </div>
      <div className={styles.metricValue}>{value}</div>
      {hint ? (
        <Text
          as="span"
          variant="caption"
          tone="muted"
          className={styles.metricHint}
        >
          {hint}
        </Text>
      ) : null}
    </Card>
  );
}
