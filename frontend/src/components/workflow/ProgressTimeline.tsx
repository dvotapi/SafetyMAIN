import { type ReactNode } from "react";

import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Workflow.module.css";

export interface ProgressTimelineItem {
  id: string;
  title: ReactNode;
  description?: ReactNode;
  timestamp?: ReactNode;
}

export interface ProgressTimelineProps {
  items: ProgressTimelineItem[];
  className?: string;
}

export function ProgressTimeline({ items, className }: ProgressTimelineProps) {
  return (
    <ol className={cx(styles.timeline, className)}>
      {items.map((item, index) => (
        <li key={item.id} className={styles.timelineItem}>
          <div className={styles.timelineRail}>
            <span className={styles.timelineDot} aria-hidden />
            {index < items.length - 1 ? (
              <span className={styles.timelineLine} aria-hidden />
            ) : null}
          </div>
          <div className={styles.timelineContent}>
            <Text variant="label">{item.title}</Text>
            {item.description ? (
              <Text tone="muted" variant="caption">
                {item.description}
              </Text>
            ) : null}
            {item.timestamp ? (
              <Text tone="muted" variant="caption">
                {item.timestamp}
              </Text>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
