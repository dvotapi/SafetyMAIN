import {
  DescriptionItem,
  DescriptionList,
  EmptyState,
  Heading,
  Panel,
  ProgressBar,
  Text,
} from "@/components";

import type {
  RiskControl,
  RiskControlImplementation,
} from "@/features/risk-controls/types/risk-control-types";
import {
  formatRiskControlEnumLabel,
  implementationStateLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateOnly } from "@/utils/format-date";

export function ImplementationSummary({
  implementation,
  status,
}: {
  implementation: RiskControlImplementation;
  status: Pick<RiskControl, "status" | "isOverdue">;
}) {
  const hasPlan =
    implementation.targetCompletionDate !== null ||
    implementation.milestones.length > 0;

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
      <Panel>
        <Heading level={2}>Implementation</Heading>
        <Text>
          {implementationStateLabel({
            status: status.status,
            progress: implementation.progress,
            actualCompletionDate: implementation.actualCompletionDate,
          })}
        </Text>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <ProgressBar
              value={implementation.progress}
              label="Implementation progress"
            />
          </div>
          <Text variant="caption">{implementation.progress}%</Text>
        </div>

        {hasPlan ? (
          <>
            <DescriptionList>
              <DescriptionItem
                term="Target start date"
                details={formatDateOnly(implementation.targetStartDate)}
              />
              <DescriptionItem
                term="Target completion date"
                details={formatDateOnly(implementation.targetCompletionDate)}
              />
              <DescriptionItem
                term="Actual start date"
                details={formatDateOnly(implementation.actualStartDate)}
              />
              <DescriptionItem
                term="Actual completion date"
                details={formatDateOnly(implementation.actualCompletionDate)}
              />
              <DescriptionItem
                term="Method"
                details={implementation.implementationMethod || "—"}
              />
              <DescriptionItem
                term="Dependencies"
                details={
                  implementation.dependencies.length > 0
                    ? implementation.dependencies.join(", ")
                    : "—"
                }
              />
              <DescriptionItem
                term="Resource notes"
                details={implementation.resourceNotes || "—"}
              />
              <DescriptionItem
                term="Evidence requirements"
                details={
                  implementation.evidenceRequirements.length > 0
                    ? implementation.evidenceRequirements.join(", ")
                    : "—"
                }
              />
              <DescriptionItem
                term="Evidence waiver reason"
                details={implementation.evidenceWaiverReason ?? "—"}
              />
            </DescriptionList>

            <Heading level={3}>Milestones</Heading>
            {implementation.milestones.length > 0 ? (
              <DescriptionList>
                {implementation.milestones.map((milestone, index) => (
                  <DescriptionItem
                    key={milestone.id ?? `milestone-${index}`}
                    term={milestone.title}
                    details={[
                      formatRiskControlEnumLabel(milestone.status),
                      milestone.dueDate
                        ? `Due: ${formatDateOnly(milestone.dueDate)}`
                        : null,
                      milestone.completedAt
                        ? `Completed: ${formatDateOnly(milestone.completedAt)}`
                        : null,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  />
                ))}
              </DescriptionList>
            ) : (
              <Text tone="muted">No milestones recorded.</Text>
            )}
          </>
        ) : (
          <EmptyState title="No implementation plan yet" />
        )}
      </Panel>
    </div>
  );
}
