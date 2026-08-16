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
        title="История недоступна"
        description="Для просмотра истории опасности нужно право audit:read. Клиентская история не формируется."
      />
    );
  }

  if (loading) {
    return (
      <EmptyState
        title="Загрузка истории"
        description="Получение событий аудита…"
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Истории пока нет"
        description="Для этой опасности нет событий аудита."
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
      item.actorUserId ? `Пользователь ${item.actorUserId}` : null,
    ]
      .filter(Boolean)
      .join(" · "),
  }));

  return <Timeline events={events} />;
}
