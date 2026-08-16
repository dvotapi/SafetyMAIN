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
    <Panel heading="Immutable snapshot captured when this control was materialized.">
      {source.snapshot ? (
        <DescriptionList>
          <DescriptionItem
            term="Source type"
            details={formatRiskControlEnumLabel(source.sourceType)}
          />
          <DescriptionItem
            term="Source control reference"
            details={source.sourceControlReference ?? "—"}
          />
          <DescriptionItem
            term="Assessment version"
            details={
              source.assessmentVersion !== null
                ? String(source.assessmentVersion)
                : "—"
            }
          />
          <DescriptionItem
            term="Assessment approved at"
            details={formatDateOnly(source.assessmentApprovedAt)}
          />
          <DescriptionItem
            term="Residual level"
            details={source.residualLevel ?? "—"}
          />
          <DescriptionItem
            term="Control type"
            details={source.snapshot.control_type ?? "—"}
          />
          <DescriptionItem
            term="Description"
            details={source.snapshot.description ?? "—"}
          />
          <DescriptionItem
            term="Responsible"
            details={source.snapshot.responsible ?? "—"}
          />
        </DescriptionList>
      ) : (
        <EmptyState
          title="No source snapshot"
          description="This control was not created from a risk assessment proposed control."
        />
      )}
    </Panel>
  );
}
