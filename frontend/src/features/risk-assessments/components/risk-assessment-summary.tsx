import Link from "next/link";

import {
  DescriptionItem,
  DescriptionList,
  Heading,
  Panel,
  PropertyGrid,
  StatusBadge,
  Text,
} from "@/components";

import type {
  ControlMeasure,
  RiskAssessment,
  RiskEvaluation,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { getAssessmentProfileCatalogEntry } from "@/features/risk-assessments/utils/assessment-profiles";
import { controlTypeLabel } from "@/features/risk-assessments/utils/hierarchy-of-controls";
import {
  formatRiskAssessmentEnumLabel,
  riskAssessmentStatusLabel,
  riskAssessmentStatusToVisual,
  riskLevelLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";

function formatDate(value: string | null | undefined): string {
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

function EvaluationPanel({
  title,
  evaluation,
}: {
  title: string;
  evaluation: RiskEvaluation | null;
}) {
  if (!evaluation) {
    return (
      <Panel>
        <Heading level={2}>{title}</Heading>
        <Text tone="muted">Not recorded.</Text>
      </Panel>
    );
  }

  return (
    <Panel>
      <Heading level={2}>{title}</Heading>
      <DescriptionList>
        <DescriptionItem
          term="Level"
          details={riskLevelLabel(evaluation.level) ?? "—"}
        />
        <DescriptionItem
          term="Factors"
          details={
            evaluation.factors.length > 0
              ? evaluation.factors
                  .map((factor) => `${factor.factor}: ${factor.score}`)
                  .join(", ")
              : "—"
          }
        />
        <DescriptionItem
          term="Explanation"
          details={evaluation.explanation || "—"}
        />
      </DescriptionList>
    </Panel>
  );
}

function ControlsPanel({ controls }: { controls: ControlMeasure[] }) {
  return (
    <Panel>
      <Heading level={2}>Proposed controls</Heading>
      {controls.length === 0 ? (
        <Text tone="muted">No proposed controls.</Text>
      ) : (
        <DescriptionList>
          {controls.map((control, index) => (
            <DescriptionItem
              key={control.id ?? `control-${index}`}
              term={controlTypeLabel(control.controlType)}
              details={[
                control.description,
                control.responsible
                  ? `Responsible: ${control.responsible}`
                  : null,
                control.implemented ? "Implemented" : "Not implemented",
                control.effective === null
                  ? null
                  : control.effective
                    ? "Effective"
                    : "Not effective",
              ]
                .filter(Boolean)
                .join(" · ")}
            />
          ))}
        </DescriptionList>
      )}
    </Panel>
  );
}

export function RiskAssessmentSummary({
  assessment,
}: {
  assessment: RiskAssessment;
}) {
  const profile = getAssessmentProfileCatalogEntry(
    assessment.assessmentProfile,
  );

  return (
    <Panel>
      <PropertyGrid columns={2}>
        <div>
          <Text variant="caption" tone="muted">
            Reference
          </Text>
          <Text>{assessment.code}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Status
          </Text>
          <StatusBadge
            status={riskAssessmentStatusToVisual(assessment.status)}
          />
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Profile
          </Text>
          <Text>{profile?.title ?? assessment.assessmentProfile}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Inherent / Residual
          </Text>
          <Text>
            {riskLevelLabel(assessment.inherentRisk?.level) ?? "—"} /{" "}
            {riskLevelLabel(assessment.residualRisk?.level) ?? "—"}
          </Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Updated
          </Text>
          <Text>{formatDate(assessment.updatedAt)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Version
          </Text>
          <Text>{assessment.version}</Text>
        </div>
      </PropertyGrid>
    </Panel>
  );
}

export function RiskAssessmentProperties({
  assessment,
  relatedHazard,
}: {
  assessment: RiskAssessment;
  relatedHazard?: {
    id: string;
    code: string;
    title: string;
    status: string;
  } | null;
}) {
  const profile = getAssessmentProfileCatalogEntry(
    assessment.assessmentProfile,
  );

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-6)" }}>
      <Panel>
        <Heading level={2}>Properties</Heading>
        <DescriptionList>
          <DescriptionItem term="Title" details={assessment.title} />
          <DescriptionItem term="Code" details={assessment.code} />
          <DescriptionItem
            term="Status"
            details={riskAssessmentStatusLabel(assessment.status)}
          />
          <DescriptionItem
            term="Assessor"
            details={assessment.assessorId || "—"}
          />
          <DescriptionItem
            term="Assessment date"
            details={formatDateOnly(assessment.assessmentDate)}
          />
          <DescriptionItem
            term="Created"
            details={formatDate(assessment.createdAt)}
          />
          <DescriptionItem
            term="Updated"
            details={formatDate(assessment.updatedAt)}
          />
          <DescriptionItem
            term="Approved"
            details={formatDate(assessment.approvedAt)}
          />
          <DescriptionItem
            term="Archived"
            details={formatDate(assessment.archivedAt)}
          />
          <DescriptionItem
            term="Superseded by"
            details={assessment.supersededById ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Assessment profile</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Profile"
            details={profile?.title ?? assessment.assessmentProfile}
          />
          <DescriptionItem
            term="Matrix size"
            details={
              profile ? `${profile.matrixSize}×${profile.matrixSize}` : "—"
            }
          />
          <DescriptionItem
            term="Required factors"
            details={profile ? profile.requiredFactorIds.join(", ") : "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Assessed object</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Type"
            details={formatRiskAssessmentEnumLabel(
              assessment.assessedObject.objectType,
            )}
          />
          <DescriptionItem
            term="Reference"
            details={assessment.assessedObject.reference}
          />
        </DescriptionList>
      </Panel>

      <EvaluationPanel
        title="Inherent risk"
        evaluation={assessment.inherentRisk}
      />
      <EvaluationPanel
        title="Residual risk"
        evaluation={assessment.residualRisk}
      />
      <ControlsPanel controls={assessment.controls} />

      <Panel>
        <Heading level={2}>Acceptance</Heading>
        {assessment.acceptance ? (
          <DescriptionList>
            <DescriptionItem
              term="Decision"
              details={formatRiskAssessmentEnumLabel(
                assessment.acceptance.decision,
              )}
            />
            <DescriptionItem
              term="Justification"
              details={assessment.acceptance.justification || "—"}
            />
            <DescriptionItem
              term="Reviewer"
              details={assessment.acceptance.reviewerId ?? "—"}
            />
            <DescriptionItem
              term="Accepted at"
              details={formatDate(assessment.acceptance.approvedAt)}
            />
          </DescriptionList>
        ) : (
          <Text tone="muted">No acceptance recorded.</Text>
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Review schedule</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Due date"
            details={formatDateOnly(assessment.reviewSchedule.reviewDueDate)}
          />
          <DescriptionItem
            term="Frequency (days)"
            details={
              assessment.reviewSchedule.reviewFrequencyDays !== null
                ? String(assessment.reviewSchedule.reviewFrequencyDays)
                : "—"
            }
          />
          <DescriptionItem
            term="Reason"
            details={assessment.reviewSchedule.reviewReason ?? "—"}
          />
          <DescriptionItem
            term="Triggered by"
            details={assessment.reviewSchedule.triggeredBy ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Competency requirements</Heading>
        {assessment.competencyRequirements.length > 0 ? (
          <Text>{assessment.competencyRequirements.join(", ")}</Text>
        ) : (
          <Text tone="muted">None recorded.</Text>
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Related Hazard</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Hazard"
            details={
              <Link href={`/safety/hazards/${assessment.hazardId}`}>
                {relatedHazard
                  ? `${relatedHazard.code} — ${relatedHazard.title}`
                  : assessment.hazardId}
              </Link>
            }
          />
          {relatedHazard ? (
            <DescriptionItem
              term="Status"
              details={formatRiskAssessmentEnumLabel(relatedHazard.status)}
            />
          ) : null}
        </DescriptionList>
      </Panel>
    </div>
  );
}
