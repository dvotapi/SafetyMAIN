"use client";

import { useMemo, useState, type ReactNode } from "react";

import { Icon } from "@/icons/Icon";
import type { IconName } from "@/icons";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Timeline.module.css";

export interface TimelineEvent {
  id: string;
  title: ReactNode;
  description?: ReactNode;
  timestamp: Date | string;
  icon?: IconName;
}

export interface TimelineProps {
  events: TimelineEvent[];
  groupByDate?: boolean;
  defaultExpandedGroups?: Record<string, boolean>;
  className?: string;
}

function toDate(value: Date | string): Date {
  return value instanceof Date ? value : new Date(value);
}

function formatAbsolute(date: Date): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatRelative(date: Date, now: Date): string {
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.round(diffMs / 60000);
  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatAbsolute(date);
}

function dateGroupKey(date: Date): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "long" }).format(date);
}

export function Timeline({
  events,
  groupByDate = true,
  defaultExpandedGroups,
  className,
}: TimelineProps) {
  const now = useMemo(() => new Date(), []);
  const grouped = useMemo(() => {
    if (!groupByDate) {
      return [{ key: "all", label: "Events", events }];
    }
    const map = new Map<string, TimelineEvent[]>();
    for (const event of events) {
      const key = dateGroupKey(toDate(event.timestamp));
      const list = map.get(key) ?? [];
      list.push(event);
      map.set(key, list);
    }
    return Array.from(map.entries()).map(([key, groupEvents]) => ({
      key,
      label: key,
      events: groupEvents,
    }));
  }, [events, groupByDate]);

  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    for (const group of grouped) {
      initial[group.key] = defaultExpandedGroups?.[group.key] ?? true;
    }
    return initial;
  });

  const renderEvent = (event: TimelineEvent) => {
    const date = toDate(event.timestamp);
    return (
      <li key={event.id} className={styles.event}>
        <div className={styles.eventIcon} aria-hidden>
          <Icon name={event.icon ?? "clock"} size="sm" decorative />
        </div>
        <div className={styles.eventBody}>
          <div className={styles.eventTitle}>{event.title}</div>
          {event.description ? (
            <div className={styles.eventDescription}>{event.description}</div>
          ) : null}
          <div className={styles.eventMeta}>
            <time dateTime={date.toISOString()} title={formatAbsolute(date)}>
              {formatRelative(date, now)}
            </time>
            <span aria-hidden>·</span>
            <span>{formatAbsolute(date)}</span>
          </div>
        </div>
      </li>
    );
  };

  return (
    <div className={cx(styles.timeline, className)}>
      {grouped.map((group) => {
        const isExpanded = expanded[group.key] ?? true;
        return (
          <section
            key={group.key}
            className={cx(styles.group, !isExpanded && styles.collapsed)}
          >
            {groupByDate ? (
              <div className={styles.groupHeader}>
                <Text as="span" variant="label" className={styles.groupTitle}>
                  {group.label}
                </Text>
                <button
                  type="button"
                  className={styles.groupToggle}
                  aria-expanded={isExpanded}
                  onClick={() =>
                    setExpanded((state) => ({
                      ...state,
                      [group.key]: !isExpanded,
                    }))
                  }
                >
                  {isExpanded ? "Collapse" : "Expand"}
                </button>
              </div>
            ) : null}
            <ul className={styles.events}>{group.events.map(renderEvent)}</ul>
          </section>
        );
      })}
    </div>
  );
}
