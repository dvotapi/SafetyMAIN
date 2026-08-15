import { cx } from "@/utils/cx";

import { ActivityItem, type ActivityItemProps } from "./ActivityItem";
import styles from "./Activity.module.css";

export type ActivityFeedItem = ActivityItemProps;

export interface ActivityFeedProps {
  items: ActivityFeedItem[];
  className?: string;
}

export function ActivityFeed({ items, className }: ActivityFeedProps) {
  return (
    <div className={cx(styles.feed, className)}>
      {items.map((item) => (
        <ActivityItem key={item.id} {...item} />
      ))}
    </div>
  );
}
