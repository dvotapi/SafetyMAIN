import { Panel } from "@/components/primitives/Surface";
import { Timeline, type TimelineEvent } from "@/components/timeline/Timeline";
import { cx } from "@/utils/cx";

import styles from "./ObjectPage.module.css";

export interface ObjectTimelineProps {
  events: TimelineEvent[];
  heading?: string;
  className?: string;
}

export function ObjectTimeline({
  events,
  heading = "Хронология",
  className,
}: ObjectTimelineProps) {
  return (
    <Panel heading={heading} className={cx(styles.panelSection, className)}>
      <Timeline events={events} />
    </Panel>
  );
}
