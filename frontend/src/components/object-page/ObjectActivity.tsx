import { Panel } from "@/components/primitives/Surface";
import {
  ActivityFeed,
  type ActivityFeedItem,
} from "@/components/activity/ActivityFeed";
import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectActivityProps {
  items: ActivityFeedItem[];
  heading?: string;
  className?: string;
}

export function ObjectActivity({
  items,
  heading = "Activity",
  className,
}: ObjectActivityProps) {
  return (
    <Panel heading={heading} className={cx(styles.panelSection, className)}>
      <ActivityFeed items={items} />
    </Panel>
  );
}
