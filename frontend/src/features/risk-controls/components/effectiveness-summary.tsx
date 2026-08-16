import Link from "next/link";

import { Alert, StatusBadge, Text } from "@/components";

import type {
  RiskControl,
  RiskControlVerification,
} from "@/features/risk-controls/types/risk-control-types";
import {
  effectivenessLabel,
  effectivenessToVisual,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly } from "@/utils/format-date";

/**
 * Read-only summary of the latest effectiveness result. Never mutates
 * residual risk and never creates a risk assessment — an ineffective or
 * partially effective verification only links back to the source
 * assessment for a human to act on.
 */
export function EffectivenessSummary({
  latestResult,
  latestVerification,
  riskAssessmentId,
}: {
  latestResult: RiskControl["latestEffectivenessResult"];
  latestVerification: RiskControlVerification | null;
  riskAssessmentId?: string | null;
}) {
  const visual = effectivenessToVisual(latestResult);
  const label = effectivenessLabel(latestResult);

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        {visual ? (
          <StatusBadge status={visual} label={label} />
        ) : (
          <Text>{label}</Text>
        )}
        {latestVerification ? (
          <Text variant="caption" tone="muted">
            {formatRiskControlEnumLabel(latestVerification.verificationType)} ·{" "}
            {formatDateOnly(latestVerification.performedAt)}
          </Text>
        ) : null}
      </div>

      {latestResult === "ineffective" ? (
        <Alert tone="danger" title="Control verified ineffective">
          <Text>
            This control did not achieve its intended effect. Review the source
            risk assessment and plan corrective action.
          </Text>
          {riskAssessmentId ? (
            <Link href={`/safety/risk-assessments/${riskAssessmentId}`}>
              View source risk assessment
            </Link>
          ) : null}
        </Alert>
      ) : null}

      {latestResult === "partially_effective" ? (
        <Alert tone="warning" title="Control verified partially effective">
          <Text>
            This control partially achieved its intended effect. Review the
            source risk assessment to decide whether further action is needed.
          </Text>
          {riskAssessmentId ? (
            <Link href={`/safety/risk-assessments/${riskAssessmentId}`}>
              View source risk assessment
            </Link>
          ) : null}
        </Alert>
      ) : null}
    </div>
  );
}
