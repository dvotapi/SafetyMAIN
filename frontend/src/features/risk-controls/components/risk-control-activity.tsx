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
        title="История недоступна"
        description="История меры требует право audit:read. Клиентская история не показывается."
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
      <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
        <EmptyState
          title="Истории пока нет"
          description="Для этой меры нет событий аудита."
        />
        <Text variant="caption" tone="muted">
          Создание фиксируется в исходной оценке риска и отображается в её
          истории.
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
      item.actorUserId ? `Исполнитель ${item.actorUserId}` : null,
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
