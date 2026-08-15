import { type HTMLAttributes, type ReactNode } from "react";

import { Card } from "@/components/primitives/Surface";
import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export interface StatisticCardProps extends HTMLAttributes<HTMLDivElement> {
  label: ReactNode;
  value: ReactNode;
  trend?: ReactNode;
  trendDirection?: "up" | "down";
}

export function StatisticCard({
  label,
  value,
  trend,
  trendDirection,
  className,
  ...rest
}: StatisticCardProps) {
  return (
    <Card className={cx(styles.statCard, className)} {...rest}>
      <div className={styles.statLabel}>{label}</div>
      <div className={styles.statValue}>{value}</div>
      {trend ? (
        <div
          className={cx(
            styles.statTrend,
            trendDirection === "up" && styles.statTrendUp,
            trendDirection === "down" && styles.statTrendDown,
          )}
        >
          {trend}
        </div>
      ) : null}
    </Card>
  );
}
