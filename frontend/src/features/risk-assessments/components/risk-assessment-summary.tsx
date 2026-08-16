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
  acceptanceDecisionLabel,
  assessedObjectTypeLabel,
  relatedHazardStatusLabel,
  riskAssessmentStatusLabel,
  riskAssessmentStatusToVisual,
  riskFactorLabel,
  riskLevelLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";
import { APP_LOCALE } from "@/utils/locale";

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(APP_LOCALE, {
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
    return new Intl.DateTimeFormat(APP_LOCALE, {
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
        <Text tone="muted">Не зафиксировано.</Text>
      </Panel>
    );
  }

  return (
    <Panel>
      <Heading level={2}>{title}</Heading>
      <DescriptionList>
        <DescriptionItem
          term="Уровень"
          details={riskLevelLabel(evaluation.level) ?? "—"}
        />
        <DescriptionItem
          term="Факторы"
          details={
            evaluation.factors.length > 0
              ? evaluation.factors
                  .map(
                    (factor) =>
                      `${riskFactorLabel(factor.factor)}: ${factor.score}`,
                  )
                  .join(", ")
              : "—"
          }
        />
        <DescriptionItem
          term="Пояснение"
          details={evaluation.explanation || "—"}
        />
      </DescriptionList>
    </Panel>
  );
}

function ControlsPanel({ controls }: { controls: ControlMeasure[] }) {
  return (
    <Panel>
      <Heading level={2}>Предлагаемые меры</Heading>
      {controls.length === 0 ? (
        <Text tone="muted">Нет предлагаемых мер.</Text>
      ) : (
        <DescriptionList>
          {controls.map((control, index) => (
            <DescriptionItem
              key={control.id ?? `control-${index}`}
              term={controlTypeLabel(control.controlType)}
              details={[
                control.description,
                control.responsible
                  ? `Ответственный: ${control.responsible}`
                  : null,
                control.implemented ? "Внедрено" : "Не внедрено",
                control.effective === null
                  ? null
                  : control.effective
                    ? "Эффективна"
                    : "Неэффективна",
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
            Код
          </Text>
          <Text>{assessment.code}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Статус
          </Text>
          <StatusBadge
            status={riskAssessmentStatusToVisual(assessment.status)}
          />
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Профиль
          </Text>
          <Text>{profile?.title ?? assessment.assessmentProfile}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Исходный / остаточный
          </Text>
          <Text>
            {riskLevelLabel(assessment.inherentRisk?.level) ?? "—"} /{" "}
            {riskLevelLabel(assessment.residualRisk?.level) ?? "—"}
          </Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Обновлено
          </Text>
          <Text>{formatDate(assessment.updatedAt)}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Версия
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
        <Heading level={2}>Свойства</Heading>
        <DescriptionList>
          <DescriptionItem term="Название" details={assessment.title} />
          <DescriptionItem term="Код" details={assessment.code} />
          <DescriptionItem
            term="Статус"
            details={riskAssessmentStatusLabel(assessment.status)}
          />
          <DescriptionItem
            term="Оценщик"
            details={assessment.assessorId || "—"}
          />
          <DescriptionItem
            term="Дата оценки"
            details={formatDateOnly(assessment.assessmentDate)}
          />
          <DescriptionItem
            term="Создано"
            details={formatDate(assessment.createdAt)}
          />
          <DescriptionItem
            term="Обновлено"
            details={formatDate(assessment.updatedAt)}
          />
          <DescriptionItem
            term="Утверждено"
            details={formatDate(assessment.approvedAt)}
          />
          <DescriptionItem
            term="Архив"
            details={formatDate(assessment.archivedAt)}
          />
          <DescriptionItem
            term="Замещено оценкой"
            details={assessment.supersededById ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Профиль оценки</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Профиль"
            details={profile?.title ?? assessment.assessmentProfile}
          />
          <DescriptionItem
            term="Размер матрицы"
            details={
              profile ? `${profile.matrixSize}×${profile.matrixSize}` : "—"
            }
          />
          <DescriptionItem
            term="Обязательные факторы"
            details={
              profile
                ? profile.requiredFactorIds
                    .map((factor) => riskFactorLabel(factor))
                    .join(", ")
                : "—"
            }
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Объект оценки</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Тип"
            details={assessedObjectTypeLabel(
              assessment.assessedObject.objectType,
            )}
          />
          <DescriptionItem
            term="Ссылка"
            details={assessment.assessedObject.reference}
          />
        </DescriptionList>
      </Panel>

      <EvaluationPanel
        title="Исходный риск"
        evaluation={assessment.inherentRisk}
      />
      <EvaluationPanel
        title="Остаточный риск"
        evaluation={assessment.residualRisk}
      />
      <ControlsPanel controls={assessment.controls} />

      <Panel>
        <Heading level={2}>Принятие</Heading>
        {assessment.acceptance ? (
          <DescriptionList>
            <DescriptionItem
              term="Решение"
              details={acceptanceDecisionLabel(assessment.acceptance.decision)}
            />
            <DescriptionItem
              term="Обоснование"
              details={assessment.acceptance.justification || "—"}
            />
            <DescriptionItem
              term="Рецензент"
              details={assessment.acceptance.reviewerId ?? "—"}
            />
            <DescriptionItem
              term="Принято"
              details={formatDate(assessment.acceptance.approvedAt)}
            />
          </DescriptionList>
        ) : (
          <Text tone="muted">Принятие не зафиксировано.</Text>
        )}
      </Panel>

      <Panel>
        <Heading level={2}>График пересмотра</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Срок"
            details={formatDateOnly(assessment.reviewSchedule.reviewDueDate)}
          />
          <DescriptionItem
            term="Периодичность (дней)"
            details={
              assessment.reviewSchedule.reviewFrequencyDays !== null
                ? String(assessment.reviewSchedule.reviewFrequencyDays)
                : "—"
            }
          />
          <DescriptionItem
            term="Причина"
            details={assessment.reviewSchedule.reviewReason ?? "—"}
          />
          <DescriptionItem
            term="Инициатор"
            details={assessment.reviewSchedule.triggeredBy ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Требования к компетенции</Heading>
        {assessment.competencyRequirements.length > 0 ? (
          <Text>{assessment.competencyRequirements.join(", ")}</Text>
        ) : (
          <Text tone="muted">Не зафиксировано.</Text>
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Связанная опасность</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Опасность"
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
              term="Статус"
              details={relatedHazardStatusLabel(relatedHazard.status)}
            />
          ) : null}
        </DescriptionList>
      </Panel>
    </div>
  );
}
