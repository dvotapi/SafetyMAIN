import Link from "next/link";

import { EmptyState, Heading, Panel, Text } from "@/components";

import type { RiskAssessmentSummary } from "@/features/hazards/types/hazard-types";
import {
  assessmentProfileLabel,
  relatedAssessmentStatusLabel,
} from "@/features/hazards/utils/hazard-status";

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
        <Text tone="muted">Загрузка сводки по рискам…</Text>
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
      <Heading level={2}>Сводка по рискам</Heading>
      <Text tone="secondary">
        Связанных оценок: {assessments.length}. Утверждённых: {approved.length}.
      </Text>
      {latestApproved ? (
        <Text>
          Последняя утверждённая:{" "}
          <Link href={`/safety/risk-assessments/${latestApproved.id}`}>
            {latestApproved.code}
          </Link>
          {latestApproved.residualRiskLabel
            ? ` · остаточный ${latestApproved.residualRiskLabel}`
            : ""}
        </Text>
      ) : (
        <Text tone="muted">Утверждённых оценок пока нет.</Text>
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
        title="Оценки риска недоступны"
        description="Недостаточно прав для просмотра связанных оценок риска."
      />
    );
  }

  if (loading) {
    return <Text tone="muted">Загрузка связанных оценок риска…</Text>;
  }

  if (assessments.length === 0) {
    return (
      <EmptyState
        title="Нет связанных оценок риска"
        description="К этой опасности пока не привязаны оценки риска."
      />
    );
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Код</th>
            <th align="left">Название</th>
            <th align="left">Статус</th>
            <th align="left">Профиль</th>
            <th align="left">Исходный</th>
            <th align="left">Остаточный</th>
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
              <td>{relatedAssessmentStatusLabel(item.status)}</td>
              <td>{assessmentProfileLabel(item.assessmentProfile)}</td>
              <td>{item.inherentRiskLabel ?? "—"}</td>
              <td>{item.residualRiskLabel ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
