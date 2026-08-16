import Link from "next/link";

import {
  ObjectRelationships,
  Text,
  type ObjectRelationship,
} from "@/components";

import type {
  RiskControl,
  RiskControlAssessmentSummary,
  RiskControlCapabilities,
  RiskControlHazardSummary,
} from "@/features/risk-controls/types/risk-control-types";

/** Minimal shape of a react-query result this component needs. */
interface RelatedQueryState<T> {
  data: T | null | undefined;
  isError: boolean;
  isLoading: boolean;
}

/**
 * Cross-tenant masking: whether the related hazard/assessment is a genuine
 * 404 or a cross-tenant access attempt, the same "Not accessible in this
 * organization" note is shown. Never distinguish the two cases.
 */
export function RiskControlRelationships({
  control,
  hazard,
  assessment,
  capabilities,
}: {
  control: RiskControl;
  hazard: RelatedQueryState<RiskControlHazardSummary>;
  assessment: RelatedQueryState<RiskControlAssessmentSummary>;
  capabilities: RiskControlCapabilities;
}) {
  const items: ObjectRelationship[] = [];

  if (control.hazardId) {
    const accessible =
      capabilities.canViewHazard && !hazard.isError && Boolean(hazard.data);
    items.push({
      id: "hazard",
      label: "Опасность",
      value: accessible ? (
        <Link href={`/safety/hazards/${control.hazardId}`}>
          {hazard.data!.code} — {hazard.data!.title}
        </Link>
      ) : hazard.isLoading ? (
        <Text as="span" tone="muted" variant="caption">
          Загрузка…
        </Text>
      ) : (
        <>
          <Text as="span">{control.hazardId}</Text>{" "}
          <Text as="span" tone="muted" variant="caption">
            Недоступно в этой организации
          </Text>
        </>
      ),
    });
  }

  if (control.riskAssessmentId) {
    const accessible =
      capabilities.canViewAssessment &&
      !assessment.isError &&
      Boolean(assessment.data);
    items.push({
      id: "risk-assessment",
      label: "Оценка риска",
      value: accessible ? (
        <Link href={`/safety/risk-assessments/${control.riskAssessmentId}`}>
          {assessment.data!.code} — {assessment.data!.title}
        </Link>
      ) : assessment.isLoading ? (
        <Text as="span" tone="muted" variant="caption">
          Загрузка…
        </Text>
      ) : (
        <>
          <Text as="span">{control.riskAssessmentId}</Text>{" "}
          <Text as="span" tone="muted" variant="caption">
            Недоступно в этой организации
          </Text>
        </>
      ),
    });
  }

  return <ObjectRelationships items={items} />;
}
