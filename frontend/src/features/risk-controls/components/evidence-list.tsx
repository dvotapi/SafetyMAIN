import { EmptyState, Panel } from "@/components";

import type { RiskControlEvidence } from "@/features/risk-controls/types/risk-control-types";
import { formatRiskControlEnumLabel } from "@/features/risk-controls/utils/risk-control-status";

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

/**
 * Evidence is a reference, not a file — this list never renders an upload
 * control. Uploads (if ever added) belong to a future implementation-command
 * flow, not this read-only object page.
 */
export function EvidenceList({
  evidence,
}: {
  evidence: RiskControlEvidence[];
}) {
  if (evidence.length === 0) {
    return (
      <EmptyState
        title="No evidence yet"
        description="Evidence references are added during implementation."
      />
    );
  }

  return (
    <Panel>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Title</th>
            <th style={{ textAlign: "left" }}>Type</th>
            <th style={{ textAlign: "left" }}>External reference</th>
            <th style={{ textAlign: "left" }}>Captured at</th>
            <th style={{ textAlign: "left" }}>Captured by</th>
          </tr>
        </thead>
        <tbody>
          {evidence.map((item) => (
            <tr key={item.id}>
              <td>{item.title || "—"}</td>
              <td>{formatRiskControlEnumLabel(item.evidenceType)}</td>
              <td>{item.externalReference || "—"}</td>
              <td>{formatDateOnly(item.capturedAt)}</td>
              <td>{item.capturedByUserId ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
