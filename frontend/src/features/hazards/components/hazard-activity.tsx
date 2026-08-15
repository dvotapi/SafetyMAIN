import { EmptyState, Timeline, type TimelineEvent } from "@/components";

import type { HazardActivityItem } from "@/features/hazards/types/hazard-types";

export function HazardActivity({
  items,
  loading,
  canView,
}: {
  items: HazardActivityItem[];
  loading?: boolean;
  canView: boolean;
}) {
  if (!canView) {
    return (
      <EmptyState
        title="Activity unavailable"
        description="Hazard activity requires the audit:read permission. No client-generated history is shown."
      />
    );
  }

  if (loading) {
    return (
      <EmptyState
        title="Loading activity"
        description="Fetching audit events…"
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="No activity yet"
        description="No audit events are available for this hazard."
      />
    );
  }

  const events: TimelineEvent[] = items.map((item) => ({
    id: item.id,
    title: item.title,
    timestamp: item.occurredAt,
    description: [
      item.action,
      item.outcome,
      item.actorUserId ? `Actor ${item.actorUserId}` : null,
    ]
      .filter(Boolean)
      .join(" · "),
  }));

  return <Timeline events={events} />;
}
