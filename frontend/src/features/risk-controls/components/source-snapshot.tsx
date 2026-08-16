import {
  DescriptionItem,
  DescriptionList,
  EmptyState,
  Panel,
} from "@/components";

import type { RiskControlSource } from "@/features/risk-controls/types/risk-control-types";
import { formatRiskControlEnumLabel } from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly } from "@/utils/format-date";

/** Read-only. The snapshot is immutable once materialized — no edit affordance. */
export function SourceSnapshot({ source }: { source: RiskControlSource }) {
  return (
    <Panel heading="Неизменяемый снимок на момент создания меры.">
      {source.snapshot ? (
        <DescriptionList>
          <DescriptionItem
            term="Тип источника"
            details={formatRiskControlEnumLabel(source.sourceType)}
          />
          <DescriptionItem
            term="Ссылка на исходную меру"
            details={source.sourceControlReference ?? "—"}
          />
          <DescriptionItem
            term="Версия оценки"
            details={
              source.assessmentVersion !== null
                ? String(source.assessmentVersion)
                : "—"
            }
          />
          <DescriptionItem
            term="Оценка утверждена"
            details={formatDateOnly(source.assessmentApprovedAt)}
          />
          <DescriptionItem
            term="Остаточный уровень"
            details={source.residualLevel ?? "—"}
          />
          <DescriptionItem
            term="Тип меры"
            details={source.snapshot.control_type ?? "—"}
          />
          <DescriptionItem
            term="Описание"
            details={source.snapshot.description ?? "—"}
          />
          <DescriptionItem
            term="Ответственный"
            details={source.snapshot.responsible ?? "—"}
          />
        </DescriptionList>
      ) : (
        <EmptyState
          title="Нет снимка источника"
          description="Мера не создана из предложенной меры оценки риска."
        />
      )}
    </Panel>
  );
}
