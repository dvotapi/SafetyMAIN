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
        <Alert tone="danger" title="Мера подтверждена неэффективной">
          <Text>
            Мера не достигла цели. Просмотрите исходную оценку риска и
            спланируйте корректирующие действия.
          </Text>
          {riskAssessmentId ? (
            <Link href={`/safety/risk-assessments/${riskAssessmentId}`}>
              Открыть исходную оценку риска
            </Link>
          ) : null}
        </Alert>
      ) : null}

      {latestResult === "partially_effective" ? (
        <Alert tone="warning" title="Мера подтверждена частично эффективной">
          <Text>
            Мера частично достигла цели. Просмотрите исходную оценку риска,
            чтобы решить, нужны ли дополнительные действия.
          </Text>
          {riskAssessmentId ? (
            <Link href={`/safety/risk-assessments/${riskAssessmentId}`}>
              Открыть исходную оценку риска
            </Link>
          ) : null}
        </Alert>
      ) : null}
    </div>
  );
}
