import {
  DescriptionItem,
  DescriptionList,
  Heading,
  Panel,
  PropertyGrid,
  StatusBadge,
  Text,
} from "@/components";

import type { Hazard } from "@/features/hazards/types/hazard-types";
import {
  affectedSubjectLabel,
  hazardCategoryLabel,
  hazardSourceLabel,
  hazardStatusToVisual,
  safetyDirectionLabel,
} from "@/features/hazards/utils/hazard-status";
import { APP_LOCALE } from "@/utils/locale";

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(APP_LOCALE, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function HazardSummary({ hazard }: { hazard: Hazard }) {
  return (
    <Panel>
      <PropertyGrid columns={2}>
        <div>
          <Text variant="caption" tone="muted">
            Код
          </Text>
          <Text>{hazard.code}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Статус
          </Text>
          <StatusBadge status={hazardStatusToVisual(hazard.status)} />
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Категория
          </Text>
          <Text>{hazardCategoryLabel(hazard.category)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Место
          </Text>
          <Text>{hazard.locationReference ?? "—"}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Обновлено
          </Text>
          <Text>{formatDate(hazard.updatedAt)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Версия
          </Text>
          <Text>{hazard.version}</Text>
        </div>
      </PropertyGrid>
    </Panel>
  );
}

export function HazardProperties({ hazard }: { hazard: Hazard }) {
  return (
    <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
      <Panel>
        <Heading level={2}>Сведения об опасности</Heading>
        <DescriptionList>
          <DescriptionItem term="Название" details={hazard.title} />
          <DescriptionItem
            term="Описание"
            details={hazard.description || "—"}
          />
          <DescriptionItem
            term="Категория"
            details={hazardCategoryLabel(hazard.category)}
          />
          <DescriptionItem
            term="Источник"
            details={hazardSourceLabel(hazard.source)}
          />
          <DescriptionItem
            term="Направления безопасности"
            details={
              hazard.safetyDirections.map(safetyDirectionLabel).join(", ") ||
              "—"
            }
          />
          <DescriptionItem
            term="Затронутые объекты"
            details={
              hazard.affectedSubjects.map(affectedSubjectLabel).join(", ") ||
              "—"
            }
          />
        </DescriptionList>
      </Panel>
      <Panel>
        <Heading level={2}>Место и область</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Место"
            details={hazard.locationReference ?? "—"}
          />
          <DescriptionItem
            term="Процесс"
            details={hazard.processReference ?? "—"}
          />
          <DescriptionItem
            term="Оборудование"
            details={hazard.equipmentReference ?? "—"}
          />
        </DescriptionList>
      </Panel>
      <Panel>
        <Heading level={2}>Жизненный цикл</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Статус"
            details={
              <StatusBadge status={hazardStatusToVisual(hazard.status)} />
            }
          />
          <DescriptionItem
            term="Выявлено"
            details={formatDate(hazard.identifiedAt)}
          />
          <DescriptionItem
            term="Рассмотрено"
            details={formatDate(hazard.reviewedAt)}
          />
          <DescriptionItem
            term="Архивировано"
            details={formatDate(hazard.archivedAt)}
          />
          <DescriptionItem
            term="Создано"
            details={formatDate(hazard.createdAt)}
          />
          <DescriptionItem
            term="Обновлено"
            details={formatDate(hazard.updatedAt)}
          />
        </DescriptionList>
      </Panel>
    </div>
  );
}
