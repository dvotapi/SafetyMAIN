import type { ReactNode } from "react";

import { EmptyState, Heading, Panel, Text } from "@/components";

import type {
  ControlMeasure,
  RelatedRiskControlSummary,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { relatedControlsEmptyKind } from "@/features/risk-assessments/utils/related-controls-empty";
import { formatRiskAssessmentEnumLabel } from "@/features/risk-assessments/utils/risk-assessment-status";

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
        title="Related controls unavailable"
        description="Related Risk Controls require the risk_control:read permission."
      />
    );
  }

  if (loading) {
    return (
      <EmptyState
        title="Loading related controls"
        description="Fetching materialized Risk Controls…"
      />
    );
  }

  const emptyKind = relatedControlsEmptyKind(proposedControls, controls);
  if (emptyKind === "no_proposed") {
    return (
      <EmptyState
        title="No proposed controls"
        description="This assessment has no proposed controls, so no related Risk Controls are expected yet."
      />
    );
  }
  if (emptyKind === "not_materialized") {
    return (
      <EmptyState
        title="No materialized Risk Controls"
        description="Proposed controls exist on this assessment. Use Materialize controls to create operational Risk Controls."
        action={actions}
      />
    );
  }

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-4)" }}>
      <Panel actions={actions}>
        <Heading level={2}>Related Risk Controls</Heading>
        <Text tone="secondary">
          Read-only view of materialized controls linked to this assessment.
        </Text>
      </Panel>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Reference</th>
              <th align="left">Title</th>
              <th align="left">Hierarchy</th>
              <th align="left">Status</th>
              <th align="left">Owner</th>
              <th align="left">Effectiveness</th>
              <th align="left">Next review</th>
            </tr>
          </thead>
          <tbody>
            {controls.map((item) => (
              <tr key={item.id}>
                <td>{item.code}</td>
                <td>{item.title}</td>
                <td>{formatRiskAssessmentEnumLabel(item.hierarchyLevel)}</td>
                <td>{formatRiskAssessmentEnumLabel(item.lifecycleStatus)}</td>
                <td>{item.ownerLabel ?? "—"}</td>
                <td>
                  {item.latestEffectivenessResult
                    ? formatRiskAssessmentEnumLabel(
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
