import {
  DescriptionItem,
  DescriptionList,
  EmptyState,
  Heading,
  Panel,
  ProgressBar,
  Text,
} from "@/components";

import type {
  RiskControl,
  RiskControlImplementation,
} from "@/features/risk-controls/types/risk-control-types";
import {
  formatRiskControlEnumLabel,
  implementationStateLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly } from "@/utils/format-date";

export function ImplementationSummary({
  implementation,
  status,
}: {
  implementation: RiskControlImplementation;
  status: Pick<RiskControl, "status" | "isOverdue">;
}) {
  const hasPlan =
    implementation.targetCompletionDate !== null ||
    implementation.milestones.length > 0;

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
      <Panel>
        <Heading level={2}>Внедрение</Heading>
        <Text>
          {implementationStateLabel({
            status: status.status,
            progress: implementation.progress,
            actualCompletionDate: implementation.actualCompletionDate,
          })}
        </Text>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <ProgressBar
              value={implementation.progress}
              label="Прогресс внедрения"
            />
          </div>
          <Text variant="caption">{implementation.progress}%</Text>
        </div>

        {hasPlan ? (
          <>
            <DescriptionList>
              <DescriptionItem
                term="Плановая дата начала"
                details={formatDateOnly(implementation.targetStartDate)}
              />
              <DescriptionItem
                term="Плановая дата завершения"
                details={formatDateOnly(implementation.targetCompletionDate)}
              />
              <DescriptionItem
                term="Фактическая дата начала"
                details={formatDateOnly(implementation.actualStartDate)}
              />
              <DescriptionItem
                term="Фактическая дата завершения"
                details={formatDateOnly(implementation.actualCompletionDate)}
              />
              <DescriptionItem
                term="Метод"
                details={implementation.implementationMethod || "—"}
              />
              <DescriptionItem
                term="Зависимости"
                details={
                  implementation.dependencies.length > 0
                    ? implementation.dependencies.join(", ")
                    : "—"
                }
              />
              <DescriptionItem
                term="Заметки о ресурсах"
                details={implementation.resourceNotes || "—"}
              />
              <DescriptionItem
                term="Требования к доказательствам"
                details={
                  implementation.evidenceRequirements.length > 0
                    ? implementation.evidenceRequirements.join(", ")
                    : "—"
                }
              />
              <DescriptionItem
                term="Причина отказа от доказательств"
                details={implementation.evidenceWaiverReason ?? "—"}
              />
            </DescriptionList>

            <Heading level={3}>Вехи</Heading>
            {implementation.milestones.length > 0 ? (
              <DescriptionList>
                {implementation.milestones.map((milestone, index) => (
                  <DescriptionItem
                    key={milestone.id ?? `milestone-${index}`}
                    term={milestone.title}
                    details={[
                      formatRiskControlEnumLabel(milestone.status),
                      milestone.dueDate
                        ? `Срок: ${formatDateOnly(milestone.dueDate)}`
                        : null,
                      milestone.completedAt
                        ? `Завершено: ${formatDateOnly(milestone.completedAt)}`
                        : null,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  />
                ))}
              </DescriptionList>
            ) : (
              <Text tone="muted">Вехи не зафиксированы.</Text>
            )}
          </>
        ) : (
          <EmptyState title="Плана внедрения пока нет" />
        )}
      </Panel>
    </div>
  );
}
