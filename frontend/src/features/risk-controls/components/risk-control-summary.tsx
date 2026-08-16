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
import { formatDateOnly, formatDateTime } from "@/utils/format-date";

export function RiskControlSummary({ control }: { control: RiskControl }) {
  return (
    <ObjectSummary>
      <PropertyGrid columns={3}>
        <div>
          <Text variant="caption" tone="muted">
            Owner
          </Text>
          <Text>{control.owner?.label || "Не назначен"}</Text>
        </div>
        <div>
          <Text variant="caption" tone="muted">
            Иерархия мер управления
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
            Оценка риска
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
            Следующий пересмотр
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
        <Heading level={2}>Сведения о мере</Heading>
        <DescriptionList>
          <DescriptionItem term="Код" details={control.code} />
          <DescriptionItem term="Название" details={control.title} />
          <DescriptionItem
            term="Описание"
            details={control.description || "—"}
          />
          <DescriptionItem
            term="Характер меры"
            details={formatRiskControlEnumLabel(control.controlNature)}
          />
          <DescriptionItem
            term="Требование к методу подтверждения"
            details={control.verificationMethodRequirement || "—"}
          />
          <DescriptionItem
            term="Область"
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
        <Heading level={2}>Иерархия мер управления</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Уровень"
            details={formatRiskControlEnumLabel(control.hierarchyLevel)}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Владелец</Heading>
        {control.owner ? (
          <DescriptionList>
            <DescriptionItem term="Владелец" details={control.owner.label} />
            <DescriptionItem
              term="Тип владельца"
              details={formatRiskControlEnumLabel(control.owner.ownerType)}
            />
            <DescriptionItem
              term="Назначен"
              details={formatDateTime(control.owner.assignedAt)}
            />
            <DescriptionItem
              term="Назначил"
              details={control.owner.assignedBy ?? "—"}
            />
          </DescriptionList>
        ) : (
          <Text tone="muted">Не назначен.</Text>
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Исходная оценка риска</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Опасность"
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
            term="Оценка риска"
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
            term="Тип источника"
            details={formatRiskControlEnumLabel(control.source.sourceType)}
          />
          <DescriptionItem
            term="Ссылка на исходную меру"
            details={control.source.sourceControlReference ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>График пересмотра</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Пересмотр требуется"
            details={control.reviewSchedule.reviewRequired ? "Да" : "Нет"}
          />
          <DescriptionItem
            term="Частота (дней)"
            details={
              control.reviewSchedule.reviewFrequencyDays !== null
                ? String(control.reviewSchedule.reviewFrequencyDays)
                : "—"
            }
          />
          <DescriptionItem
            term="Дата следующего пересмотра"
            details={formatDateOnly(control.reviewSchedule.nextReviewDate)}
          />
          <DescriptionItem
            term="Дата последнего пересмотра"
            details={formatDateOnly(control.reviewSchedule.lastReviewDate)}
          />
          <DescriptionItem
            term="Основание пересмотра"
            details={formatRiskControlEnumLabel(
              control.reviewSchedule.reviewBasis,
            )}
          />
          <DescriptionItem
            term="Политика эскалации"
            details={control.reviewSchedule.escalationPolicyRef ?? "—"}
          />
          <DescriptionItem
            term="Причина отказа от пересмотра"
            details={control.reviewSchedule.noReviewReason ?? "—"}
          />
        </DescriptionList>
      </Panel>

      <Panel>
        <Heading level={2}>Ссылки на компетенции</Heading>
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
          <EmptyState title="Нет ссылок на компетенции" />
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Связанные объекты</Heading>
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
          <EmptyState title="Нет связанных объектов" />
        )}
      </Panel>

      <Panel>
        <Heading level={2}>Метаданные жизненного цикла</Heading>
        <DescriptionList>
          <DescriptionItem
            term="Создано"
            details={formatDateTime(control.createdAt)}
          />
          <DescriptionItem
            term="Обновлено"
            details={formatDateTime(control.updatedAt)}
          />
          <DescriptionItem term="Версия" details={String(control.version)} />
        </DescriptionList>
      </Panel>
    </div>
  );
}
