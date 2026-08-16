import type { VisualStatus } from "@/components";

import type {
  AcceptanceDecisionDto,
  AssessedObjectTypeDto,
  AssessmentProfileDto,
  RiskAssessmentStatusDto,
  RiskFactorId,
  RiskLevelDto,
} from "@/features/risk-assessments/types/risk-assessment-types";

const STATUS_TO_VISUAL: Record<RiskAssessmentStatusDto, VisualStatus> = {
  draft: "draft",
  under_review: "under_review",
  approved: "approved",
  superseded: "superseded",
  archived: "archived",
};

const STATUS_LABELS: Record<RiskAssessmentStatusDto, string> = {
  draft: "Черновик",
  under_review: "На рассмотрении",
  approved: "Утверждено",
  superseded: "Замещено",
  archived: "Архив",
};

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  extreme: "Крайний",
};

const ASSESSMENT_PROFILE_LABELS: Record<AssessmentProfileDto, string> = {
  simple_3x3: "Простая матрица 3×3",
  simple_5x5: "Простая матрица 5×5",
  corporate_custom: "Корпоративная",
  russian_occupational_risk: "Профессиональный риск (РФ)",
  industrial_safety: "Промышленная безопасность",
  fire_safety: "Пожарная безопасность",
  environmental_risk: "Экологический риск",
  transport_risk: "Транспортный риск",
  adr_risk: "Риск ДОПОГ (ADR)",
};

const ASSESSED_OBJECT_TYPE_LABELS: Record<AssessedObjectTypeDto, string> = {
  workplace: "Рабочее место",
  job_position: "Должность",
  work_activity: "Вид работ",
  equipment: "Оборудование",
  vehicle: "Транспортное средство",
  production_process: "Производственный процесс",
  location: "Место",
  contractor_activity: "Деятельность подрядчика",
  chemical: "Химическое вещество",
  emergency_scenario: "Аварийный сценарий",
};

const ACCEPTANCE_DECISION_LABELS: Record<AcceptanceDecisionDto, string> = {
  accepted: "Принят",
  conditionally_accepted: "Принят условно",
  not_accepted: "Не принят",
  requires_escalation: "Требует эскалации",
};

const RISK_FACTOR_LABELS: Record<RiskFactorId, string> = {
  probability: "Вероятность",
  severity: "Тяжесть",
  exposure: "Экспозиция",
  frequency: "Частота",
  detectability: "Обнаружимость",
  environmental_impact: "Экологическое воздействие",
  fire_consequence: "Последствия пожара",
  business_impact: "Влияние на бизнес",
};

/** Related Risk Control rows (Phase D owns full RC maps). */
const RELATED_CONTROL_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  planned: "Запланировано",
  in_implementation: "Внедряется",
  implemented: "Внедрено",
  verified_effective: "Подтверждена эффективной",
  verified_ineffective: "Подтверждена неэффективной",
  suspended: "Приостановлено",
  superseded: "Замещено",
  archived: "Архив",
  cancelled: "Отменено",
};

const RELATED_CONTROL_EFFECTIVENESS_LABELS: Record<string, string> = {
  effective: "Подтверждена эффективной",
  partially_effective: "Подтверждена частично эффективной",
  ineffective: "Подтверждена неэффективной",
  not_verified: "Не подтверждена",
  not_applicable: "Не применяется",
};

const HAZARD_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  active: "Действует",
  archived: "Архив",
};

export function riskAssessmentStatusToVisual(
  status: RiskAssessmentStatusDto,
): VisualStatus {
  return STATUS_TO_VISUAL[status];
}

export function riskAssessmentStatusLabel(
  status: RiskAssessmentStatusDto,
): string {
  return STATUS_LABELS[status];
}

export function riskLevelLabel(
  level: string | null | undefined,
): string | null {
  if (!level) {
    return null;
  }
  return RISK_LEVEL_LABELS[level.toLowerCase()] ?? level;
}

export function assessmentProfileLabel(code: string): string {
  return ASSESSMENT_PROFILE_LABELS[code as AssessmentProfileDto] ?? code;
}

export function assessedObjectTypeLabel(value: string): string {
  return ASSESSED_OBJECT_TYPE_LABELS[value as AssessedObjectTypeDto] ?? value;
}

export function acceptanceDecisionLabel(value: string): string {
  return ACCEPTANCE_DECISION_LABELS[value as AcceptanceDecisionDto] ?? value;
}

export function riskFactorLabel(value: string): string {
  return RISK_FACTOR_LABELS[value as RiskFactorId] ?? value;
}

export function relatedControlStatusLabel(value: string): string {
  return RELATED_CONTROL_STATUS_LABELS[value] ?? value;
}

export function relatedControlEffectivenessLabel(value: string): string {
  return RELATED_CONTROL_EFFECTIVENESS_LABELS[value] ?? value;
}

export function relatedHazardStatusLabel(value: string): string {
  return HAZARD_STATUS_LABELS[value] ?? value;
}

export function isRiskLevelDto(value: string): value is RiskLevelDto {
  return (
    value === "low" ||
    value === "medium" ||
    value === "high" ||
    value === "extreme"
  );
}
