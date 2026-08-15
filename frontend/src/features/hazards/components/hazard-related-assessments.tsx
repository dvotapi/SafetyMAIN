import Link from "next/link";

import { EmptyState, Heading, Panel, Text } from "@/components";

import type { RiskAssessmentSummary } from "@/features/hazards/types/hazard-types";
import { formatHazardEnumLabel } from "@/features/hazards/utils/hazard-status";

export function HazardRiskSummary({
  assessments,
  loading,
}: {
  assessments: RiskAssessmentSummary[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <Panel>
        <Text tone="muted">Loading risk summary…</Text>
      </Panel>
    );
  }

  const approved = assessments.filter((item) => item.status === "approved");
  const latestApproved = [...approved].sort((a, b) => {
    const aTime = a.approvedAt ? Date.parse(a.approvedAt) : 0;
    const bTime = b.approvedAt ? Date.parse(b.approvedAt) : 0;
    return bTime - aTime;
  })[0];

  return (
    <Panel>
      <Heading level={2}>Risk summary</Heading>
      <Text tone="secondary">
        Linked assessments: {assessments.length}. Approved: {approved.length}.
      </Text>
      {latestApproved ? (
        <Text>
          Latest approved:{" "}
          <Link href={`/safety/risk-assessments/${latestApproved.id}`}>
            {latestApproved.code}
          </Link>
          {latestApproved.residualRiskLabel
            ? ` · residual ${latestApproved.residualRiskLabel}`
            : ""}
        </Text>
      ) : (
        <Text tone="muted">No approved assessments yet.</Text>
      )}
    </Panel>
  );
}

export function HazardRelatedAssessments({
  assessments,
  loading,
  canView,
}: {
  assessments: RiskAssessmentSummary[];
  loading?: boolean;
  canView: boolean;
}) {
  if (!canView) {
    return (
      <EmptyState
        title="Risk assessments unavailable"
        description="You do not have permission to view related risk assessments."
      />
    );
  }

  if (loading) {
    return <Text tone="muted">Loading related risk assessments…</Text>;
  }

  if (assessments.length === 0) {
    return (
      <EmptyState
        title="No related risk assessments"
        description="No risk assessments are currently linked to this hazard."
      />
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Reference</th>
            <th align="left">Title</th>
            <th align="left">Status</th>
            <th align="left">Profile</th>
            <th align="left">Inherent</th>
            <th align="left">Residual</th>
          </tr>
        </thead>
        <tbody>
          {assessments.map((item) => (
            <tr key={item.id}>
              <td>
                <Link href={`/safety/risk-assessments/${item.id}`}>
                  {item.code}
                </Link>
              </td>
              <td>
                <Link href={`/safety/risk-assessments/${item.id}`}>
                  {item.title}
                </Link>
              </td>
              <td>{formatHazardEnumLabel(item.status)}</td>
              <td>{formatHazardEnumLabel(item.assessmentProfile)}</td>
              <td>{item.inherentRiskLabel ?? "—"}</td>
              <td>{item.residualRiskLabel ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
