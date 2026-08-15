import Link from "next/link";

import { ObjectSummary, Panel, PropertyGrid, Text } from "@/components";
import {
  DescriptionItem,
  DescriptionList,
  EmptyState,
  Heading,
} from "@/components";

import type {
  RiskControl,
  RiskControlAssessmentSummary,
  RiskControlHazardSummary,
} from "@/features/risk-controls/types/risk-control-types";
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

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function RiskControlSummary({ control }: { control: RiskControl }) {
  return (
    <ObjectSummary>
      <PropertyGrid columns={3}>
        <div>
          <Text variant="caption" tone="muted">
            Owner
          </Text>
          <Text>{control.owner?.label || "Unassigned"}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Hierarchy of Controls
          </Text>
          <Text>{formatRiskControlEnumLabel(control.hierarchyLevel)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Hazard
          </Text>
          <Text>
            {control.hazardId ? (
              <Link href={`/safety/hazards/${control.hazardId}`}>
                {control.hazardId}
              </Link>
            ) : (
              "—"
            )}
          </Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Risk Assessment
          </Text>
          <Text>
            {control.riskAssessmentId ? (
              <Link
                href={`/safety/risk-assessments/${control.riskAssessmentId}`}
              >
                {control.riskAssessmentId}
              </Link>
            ) : (
              "—"
            )}
          </Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Next review
          </Text>
          <Text>{formatDateOnly(control.nextReviewDate)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Version
          </Text>
          <Text>{control.version}</Text>
        </div>
      </PropertyGrid>
    </ObjectSummary>
  );
}

export function RiskControlProperties({
  control,
  hazard,
  assessment,
}: {
  control: RiskControl;
  hazard: RiskControlHazardSummary | null | undefined;
  assessment: RiskControlAssessmentSummary | null | undefined;
}) {
  return (
    <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
      <Panel>
        <Heading level={2}>Control details</Heading>
        <DescriptionList>
          <DescriptionItem term="Code" details={control.code} />
          <DescriptionItem term="Title" details={control.title} />
          <DescriptionItem
            term="Description"
            details={control.description || "—"}
          />
          <DescriptionItem
            term="Control nature"
            details={formatRiskControlEnumLabel(control.controlNature)}
          />
          <DescriptionItem
            term="Verification method requirement"
            details={control.verificationMethodRequirement || "—"}
          />
          <DescriptionItem
            term="Scope"
            details={
              control.scope.length > 0
                ? control.scope
                    .map(
                      (item) =>
                        `${formatRiskControlEnumLabel(item.scope_type)}: ${item.reference}`,
                    )
                    .join(", ")
                : "—"
            }
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Hierarchy of Controls</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Level"
            details={formatRiskControlEnumLabel(control.hierarchyLevel)}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Owner</Heading>
        {control.owner ? (
          <DescriptionList>
            <DescriptionItem term="Owner" details={control.owner.label} />
            <DescriptionItem
              term="Owner type"
              details={formatRiskControlEnumLabel(control.owner.ownerType)}
            />
            <DescriptionItem
              term="Assigned at"
              details={formatDateTime(control.owner.assignedAt)}
            />
            <DescriptionItem
              term="Assigned by"
              details={control.owner.assignedBy ?? "—"}
            />
          </DescriptionList>
        ) : (
          <Text tone="muted">Unassigned.</Text>
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Source Risk Assessment</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Hazard"
            details={
              control.hazardId ? (
                <Link href={`/safety/hazards/${control.hazardId}`}>
                  {hazard
                    ? `${hazard.code} — ${hazard.title}`
                    : control.hazardId}
                </Link>
              ) : (
                "—"
              )
            }
          />
          <DescriptionItem
            term="Risk assessment"
            details={
              control.riskAssessmentId ? (
                <Link
                  href={`/safety/risk-assessments/${control.riskAssessmentId}`}
                >
                  {assessment
                    ? `${assessment.code} — ${assessment.title}`
                    : control.riskAssessmentId}
                </Link>
              ) : (
                "—"
              )
            }
          />
          <DescriptionItem
            term="Source type"
            details={formatRiskControlEnumLabel(control.source.sourceType)}
          />
          <DescriptionItem
            term="Source control reference"
            details={control.source.sourceControlReference ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Review schedule</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Review required"
            details={control.reviewSchedule.reviewRequired ? "Yes" : "No"}
          />
          <DescriptionItem
            term="Frequency (days)"
            details={
              control.reviewSchedule.reviewFrequencyDays !== null
                ? String(control.reviewSchedule.reviewFrequencyDays)
                : "—"
            }
          />
          <DescriptionItem
            term="Next review date"
            details={formatDateOnly(control.reviewSchedule.nextReviewDate)}
          />
          <DescriptionItem
            term="Last review date"
            details={formatDateOnly(control.reviewSchedule.lastReviewDate)}
          />
          <DescriptionItem
            term="Review basis"
            details={formatRiskControlEnumLabel(
              control.reviewSchedule.reviewBasis,
            )}
          />
          <DescriptionItem
            term="Escalation policy"
            details={control.reviewSchedule.escalationPolicyRef ?? "—"}
          />
          <DescriptionItem
            term="No-review reason"
            details={control.reviewSchedule.noReviewReason ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Competency references</Heading>
        {control.competencyRequirements.length > 0 ? (
          <DescriptionList>
            {control.competencyRequirements.map((item, index) => (
              <DescriptionItem
                key={`${item.competency_ref}-${index}`}
                term={item.competency_ref}
                details={[
                  formatRiskControlEnumLabel(item.requirement_type),
                  item.required_level ? `Level: ${item.required_level}` : null,
                  item.training_program_ref
                    ? `Program: ${item.training_program_ref}`
                    : null,
                  item.notes || null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              />
            ))}
          </DescriptionList>
        ) : (
          <EmptyState title="No competency references" />
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Related entities</Heading>
        {control.relatedEntities.length > 0 ? (
          <DescriptionList>
            {control.relatedEntities.map((item, index) => (
              <DescriptionItem
                key={`${item.entity_type}-${item.reference}-${index}`}
                term={formatRiskControlEnumLabel(item.entity_type)}
                details={item.reference}
              />
            ))}
          </DescriptionList>
        ) : (
          <EmptyState title="No related entities" />
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Lifecycle metadata</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Created"
            details={formatDateTime(control.createdAt)}
          />
          <DescriptionItem
            term="Updated"
            details={formatDateTime(control.updatedAt)}
          />
          <DescriptionItem term="Version" details={String(control.version)} />
        </DescriptionList>
      </Panel>
    </div>
  );
}
