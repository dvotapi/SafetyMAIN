import { type ReactNode } from "react";

import { Avatar } from "@/components/data-display/Avatar";
import { cx } from "@/utils/cx";

import styles from "./Activity.module.css";

export interface ActivityItemProps {
  id: string;
  actorName: string;
  actorSrc?: string;
  summary: ReactNode;
  timestamp?: ReactNode;
  className?: string;
}

export function ActivityItem({
  actorName,
  actorSrc,
  summary,
  timestamp,
  className,
}: ActivityItemProps) {
  return (
    <article className={cx(styles.item, className)}>
      <Avatar
        name={actorName}
        {...(actorSrc ? { src: actorSrc } : {})}
        size="md"
      />
      <div className={styles.itemBody}>
        <div className={styles.itemSummary}>{summary}</div>
        {timestamp}
      </div>
    </article>
  );
}
