import type { ReactNode } from "react";

import { EmptyState, Heading, Panel, Text } from "@/components";

import type {
  ControlMeasure,
  ControlTypeDto,
  RelatedRiskControlSummary,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { controlTypeLabel } from "@/features/risk-assessments/utils/hierarchy-of-controls";
import { relatedControlsEmptyKind } from "@/features/risk-assessments/utils/related-controls-empty";
import {
  relatedControlEffectivenessLabel,
  relatedControlStatusLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";

export function RiskAssessmentRelatedControls({
  proposedControls,
  controls,
  loading,
  canView,
  actions,
}: {
  proposedControls: ControlMeasure[];
  controls: RelatedRiskControlSummary[];
  loading?: boolean;
  canView: boolean;
  actions?: ReactNode;
}) {
  if (!canView) {
    return (
      <EmptyState
        title="Связанные меры недоступны"
        description="Для просмотра связанных мер управления риском требуется право risk_control:read."
      />
    );
  }

  if (loading) {
    return (
      <EmptyState
        title="Загрузка связанных мер"
        description="Загрузка материализованных мер управления риском…"
      />
    );
  }

  const emptyKind = relatedControlsEmptyKind(proposedControls, controls);
  if (emptyKind === "no_proposed") {
    return (
      <EmptyState
        title="Нет предлагаемых мер"
        description="У этой оценки нет предлагаемых мер, поэтому связанные меры управления риском пока не ожидаются."
      />
    );
  }
  if (emptyKind === "not_materialized") {
    return (
      <EmptyState
        title="Нет материализованных мер"
        description="На оценке есть предлагаемые меры. Используйте «Создать меры», чтобы создать операционные меры управления риском."
        action={actions}
      />
    );
  }

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-4)" }}>
      <Panel actions={actions}>
        <Heading level={2}>Связанные меры управления риском</Heading>
        <Text tone="secondary">
          Только чтение материализованных мер, связанных с этой оценкой.
        </Text>
      </Panel>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Код</th>
              <th align="left">Название</th>
              <th align="left">Иерархия</th>
              <th align="left">Статус</th>
              <th align="left">Владелец</th>
              <th align="left">Эффективность</th>
              <th align="left">Следующий пересмотр</th>
            </tr>
          </thead>
          <tbody>
            {controls.map((item) => (
              <tr key={item.id}>
                <td>{item.code}</td>
                <td>{item.title}</td>
                <td>
                  {controlTypeLabel(item.hierarchyLevel as ControlTypeDto)}
                </td>
                <td>{relatedControlStatusLabel(item.lifecycleStatus)}</td>
                <td>{item.ownerLabel ?? "—"}</td>
                <td>
                  {item.latestEffectivenessResult
                    ? relatedControlEffectivenessLabel(
                        item.latestEffectivenessResult,
                      )
                    : "—"}
                </td>
                <td>{item.nextReviewDate ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
