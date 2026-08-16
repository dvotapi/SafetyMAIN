import { Button, EmptyState, Panel, Text } from "@/components";

import { EvidenceForm } from "@/features/risk-controls/components/evidence-form";
import type { EvidenceFormValues } from "@/features/risk-controls/schemas/evidence-schema";
import type {
  RiskControlCapabilities,
  RiskControlEvidence,
} from "@/features/risk-controls/types/risk-control-types";
import {
  TERMINAL_INACTIVE_STATUSES,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly } from "@/utils/format-date";

/**
 * Evidence is a reference, not a file — this list (and the add-evidence
 * form it opens) never renders an upload control. Evidence records only
 * point at external systems, documents, or checksums.
 */
export function EvidenceList({
  evidence,
  status,
  version,
  capabilities,
  open,
  onOpenChange,
  onAdd,
  loading = false,
  errorMessage = null,
}: {
  evidence: RiskControlEvidence[];
  status: string;
  version: number;
  capabilities: RiskControlCapabilities;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (values: EvidenceFormValues) => void | Promise<void>;
  loading?: boolean;
  errorMessage?: string | null;
}) {
  const canAdd =
    capabilities.canImplement && !TERMINAL_INACTIVE_STATUSES.has(status);

  return (
    <>
      <Panel
        heading={<Text variant="label">Evidence</Text>}
        actions={
          canAdd ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenChange(true)}
            >
              Add evidence
            </Button>
          ) : null
        }
      >
        {evidence.length === 0 ? (
          <EmptyState
            title="No evidence yet"
            description="Evidence references are added during implementation."
          />
        ) : (
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
        )}
      </Panel>

      <EvidenceForm
        status={status}
        version={version}
        open={open}
        onOpenChange={onOpenChange}
        onSubmit={onAdd}
        loading={loading}
        errorMessage={errorMessage}
      />
    </>
  );
}
