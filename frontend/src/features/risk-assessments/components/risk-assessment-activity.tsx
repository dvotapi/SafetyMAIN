import { EmptyState, Timeline, type TimelineEvent } from "@/components";

import type { RiskAssessmentActivityItem } from "@/features/risk-assessments/types/risk-assessment-types";

export function RiskAssessmentActivity({
  items,
  loading,
  canView,
}: {
  items: RiskAssessmentActivityItem[];
  loading?: boolean;
  canView: boolean;
}) {
  if (!canView) {
    return (
      <EmptyState
        title="Activity unavailable"
        description="Risk assessment activity requires the audit:read permission. No client-generated history is shown."
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
        description="No audit events are available for this risk assessment."
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
