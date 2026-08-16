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
        title="История недоступна"
        description="Для просмотра истории оценки риска требуется право audit:read. Клиентская история не показывается."
      />
    );
  }

  if (loading) {
    return (
      <EmptyState
        title="Загрузка истории"
        description="Загрузка событий аудита…"
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Истории пока нет"
        description="Для этой оценки риска нет доступных событий аудита."
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
      item.actorUserId ? `Исполнитель ${item.actorUserId}` : null,
    ]
      .filter(Boolean)
      .join(" · "),
  }));

  return <Timeline events={events} />;
}
