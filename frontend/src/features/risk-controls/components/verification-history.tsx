import { Badge, EmptyState, Panel, StatusBadge, Text } from "@/components";

import type { RiskControlVerification } from "@/features/risk-controls/types/risk-control-types";
import {
  effectivenessLabel,
  effectivenessToVisual,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";

function formatDateOnly(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

/** Read-only: no edit or delete control on any historical record (spec §51). */
export function VerificationHistory({
  verifications,
}: {
  verifications: RiskControlVerification[];
}) {
  if (verifications.length === 0) {
    return <EmptyState title="No verification yet" />;
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
              {index === 0 ? <Badge>Latest</Badge> : null}
            </div>
            <dl>
              <div>
                <Text variant="caption" tone="muted">
                  Verifier
                </Text>
                <Text>{verification.performedByUserId ?? "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Method
                </Text>
                <Text>
                  {formatRiskControlEnumLabel(verification.verificationType)}
                  {verification.method ? ` · ${verification.method}` : ""}
                </Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Criteria
                </Text>
                <Text>{verification.criteria || "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Performed at
                </Text>
                <Text>{formatDateOnly(verification.performedAt)}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Findings
                </Text>
                <Text>{verification.findings || "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Evidence references
                </Text>
                <Text>
                  {verification.evidenceRefs.length > 0
                    ? verification.evidenceRefs.join(", ")
                    : "—"}
                </Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Recommendation
                </Text>
                <Text>{verification.nextAction || "—"}</Text>
              </div>
              <div>
                <Text variant="caption" tone="muted">
                  Next review date
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
