import { Badge, EmptyState, Panel, StatusBadge, Text } from "@/components";

import type { RiskControlVerification } from "@/features/risk-controls/types/risk-control-types";
import {
  effectivenessLabel,
  effectivenessToVisual,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly } from "@/utils/format-date";

/** Read-only: no edit or delete control on any historical record (spec §51). */
export function VerificationHistory({
  verifications,
}: {
  verifications: RiskControlVerification[];
}) {
  if (verifications.length === 0) {
    return <EmptyState title="Подтверждений пока нет" />;
  }

  const newestFirst = [...verifications].reverse();

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-4)" }}>
      {newestFirst.map((verification, index) => {
        const visual = effectivenessToVisual(verification.result);
        return (
          <Panel key={verification.id}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              {visual ? (
                <StatusBadge
                  status={visual}
                  label={effectivenessLabel(verification.result)}
                />
              ) : (
                <Text>{effectivenessLabel(verification.result)}</Text>
              )}
              {index === 0 ? <Badge>Последнее</Badge> : null}
            </div>
            <dl>
              <div>
                <Text variant="caption" tone="muted">
                  Проверил
                </Text>
                <Text>{verification.performedByUserId ?? "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Метод
                </Text>
                <Text>
                  {formatRiskControlEnumLabel(verification.verificationType)}
                  {verification.method ? ` · ${verification.method}` : ""}
                </Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Критерии
                </Text>
                <Text>{verification.criteria || "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Выполнено
                </Text>
                <Text>{formatDateOnly(verification.performedAt)}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Выводы
                </Text>
                <Text>{verification.findings || "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Ссылки на доказательства
                </Text>
                <Text>
                  {verification.evidenceRefs.length > 0
                    ? verification.evidenceRefs.join(", ")
                    : "—"}
                </Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Рекомендация
                </Text>
                <Text>{verification.nextAction || "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Дата следующего пересмотра
                </Text>
                <Text>{formatDateOnly(verification.nextReviewDate)}</Text>
              </div>
            </dl>
          </Panel>
        );
      })}
    </div>
  );
}
