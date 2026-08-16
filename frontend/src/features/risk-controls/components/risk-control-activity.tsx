import { EmptyState, Text, Timeline, type TimelineEvent } from "@/components";

import type { RiskControlActivityItem } from "@/features/risk-controls/types/risk-control-types";

export function RiskControlActivity({
  items,
  loading,
  canView,
}: {
  items: RiskControlActivityItem[];
  loading?: boolean;
  canView: boolean;
}) {
  if (!canView) {
    return (
      <EmptyState
        title="Activity unavailable"
        description="Risk control activity requires the audit:read permission. No client-generated history is shown."
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
      <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
        <EmptyState
          title="No activity yet"
          description="No audit events are available for this risk control."
        />
        <Text variant="caption" tone="muted">
          Materialization is recorded against the source risk assessment and
          appears in that assessment&apos;s activity.
        </Text>
      </div>
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

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
      <Timeline events={events} />
      <Text variant="caption" tone="muted">
        Materialization is recorded against the source risk assessment and
        appears in that assessment&apos;s activity.
      </Text>
    </div>
  );
}
