import { type ReactNode } from "react";

import { Card } from "@/components/primitives/Surface";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Dashboard.module.css";

export interface TaskCardProps {
  title: ReactNode;
  description?: ReactNode;
  accessory?: ReactNode;
  className?: string;
}

export function TaskCard({
  title,
  description,
  accessory,
  className,
}: TaskCardProps) {
  return (
    <Card className={cx(styles.task, className)}>
      <div className={styles.taskHeader}>
        <Text variant="label">{title}</Text>
        {accessory}
      </div>
      {description ? (
        <Text tone="muted" variant="caption">
          {description}
        </Text>
      ) : null}
    </Card>
  );
}
