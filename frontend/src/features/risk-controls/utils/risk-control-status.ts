import type { VisualStatus } from "@/components";

import type {
  ControlNatureDto,
  ControlTypeDto,
  EffectivenessResultDto,
  EvidenceTypeDto,
  MilestoneStatusDto,
  OwnerTypeDto,
  ReviewBasisDto,
  RiskControlStatusDto,
  VerifiableEffectivenessResultDto,
  VerificationTypeDto,
} from "@/features/risk-controls/types/risk-control-dto";

export const RISK_CONTROL_STATUSES: readonly RiskControlStatusDto[] = [
  "draft",
  "planned",
  "in_implementation",
  "implemented",
  "verified_effective",
  "verified_ineffective",
  "suspended",
  "superseded",
  "archived",
  "cancelled",
];

export const HIERARCHY_LEVELS: readonly ControlTypeDto[] = [
  "elimination",
  "substitution",
  "engineering",
  "administrative",
  "ppe",
];

export const CONTROL_NATURES: readonly ControlNatureDto[] = [
  "preventive",
  "detective",
  "mitigating",
  "recovery",
];

/** Only these three are accepted by the domain; the other two always 422. */
export const VERIFIABLE_RESULTS: readonly VerifiableEffectivenessResultDto[] = [
  "effective",
  "partially_effective",
  "ineffective",
];

export const EFFECTIVENESS_FILTER_VALUES: readonly EffectivenessResultDto[] = [
  "effective",
  "partially_effective",
  "ineffective",
  "not_verified",
  "not_applicable",
];

export const EVIDENCE_TYPES: readonly EvidenceTypeDto[] = [
  "document",
  "photo",
  "video",
  "inspection_record",
  "test_result",
  "work_order",
  "training_record",
  "certificate",
  "measurement",
  "approval",
  "other",
];

export const VERIFICATION_TYPES: readonly VerificationTypeDto[] = [
  "initial",
  "scheduled_review",
  "post_incident",
  "post_inspection",
  "post_change",
  "management_review",
  "other",
];

export const REVIEW_BASES: readonly ReviewBasisDto[] = [
  "fixed_interval",
  "risk_based",
  "regulatory_requirement",
  "manufacturer_requirement",
  "corporate_policy",
  "post_incident",
  "post_change",
  "manual",
];

export const OWNER_TYPES: readonly OwnerTypeDto[] = [
  "user",
  "employee",
  "role",
  "organizational_unit",
  "external_party",
];

/**
 * Statuses in which a control is terminal-inactive — mirrors the domain's
 * `_TERMINAL_INACTIVE` set (backend/core/domain/entities/risk_control.py).
 * Single source of truth: import this instead of re-declaring the set.
 */
export const TERMINAL_INACTIVE_STATUSES: ReadonlySet<string> = new Set([
  "superseded",
  "archived",
  "cancelled",
]);

/**
 * Statuses `record_verification` accepts — mirrors the domain's
 * `record_verification` guard. Single source of truth.
 */
export const VERIFY_ALLOWED_STATUSES: ReadonlySet<string> = new Set([
  "implemented",
  "verified_effective",
  "verified_ineffective",
]);

/** `_TRANSITIONS["suspend"]` sources — every non-draft, non-terminal status. */
export const SUSPEND_ALLOWED_STATUSES: ReadonlySet<string> = new Set([
  "planned",
  "in_implementation",
  "implemented",
  "verified_effective",
  "verified_ineffective",
]);

/** `_TRANSITIONS["supersede"]` sources. */
export const SUPERSEDE_ALLOWED_STATUSES: ReadonlySet<string> = new Set([
  "implemented",
  "verified_effective",
  "verified_ineffective",
  "suspended",
]);

/** `_TRANSITIONS["cancel"]` sources. */
export const CANCEL_ALLOWED_STATUSES: ReadonlySet<string> = new Set([
  "draft",
  "planned",
  "in_implementation",
  "suspended",
]);

/**
 * `_TRANSITIONS["archive"]` sources — notably not `planned` or
 * `in_implementation`, which must resolve (or be cancelled/suspended)
 * before they can be archived.
 */
export const ARCHIVE_ALLOWED_STATUSES: ReadonlySet<string> = new Set([
  "draft",
  "implemented",
  "verified_effective",
  "verified_ineffective",
  "suspended",
  "superseded",
  "cancelled",
]);

const STATUS_TO_VISUAL: Record<RiskControlStatusDto, VisualStatus> = {
  draft: "draft",
  planned: "planned",
  in_implementation: "in_implementation",
  implemented: "implemented",
  verified_effective: "verified_effective",
  verified_ineffective: "verified_ineffective",
  suspended: "suspended",
  superseded: "superseded",
  archived: "archived",
  cancelled: "cancelled",
};

const STATUS_LABELS: Record<RiskControlStatusDto, string> = {
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

const HIERARCHY_LEVEL_LABELS: Record<ControlTypeDto, string> = {
  elimination: "Устранение",
  substitution: "Замена",
  engineering: "Инженерные меры",
  administrative: "Административные меры",
  ppe: "СИЗ",
};

const CONTROL_NATURE_LABELS: Record<ControlNatureDto, string> = {
  preventive: "Предупреждающая",
  detective: "Выявляющая",
  mitigating: "Снижающая",
  recovery: "Восстановительная",
};

const EFFECTIVENESS_TO_VISUAL: Record<string, VisualStatus> = {
  effective: "verified_effective",
  partially_effective: "verified_partially_effective",
  ineffective: "verified_ineffective",
};

const EFFECTIVENESS_LABELS: Record<string, string> = {
  effective: "Подтверждена эффективной",
  partially_effective: "Подтверждена частично эффективной",
  ineffective: "Подтверждена неэффективной",
  not_verified: "Не подтверждена",
  not_applicable: "Не применяется",
};

const EVIDENCE_TYPE_LABELS: Record<EvidenceTypeDto, string> = {
  document: "Документ",
  photo: "Фото",
  video: "Видео",
  inspection_record: "Запись проверки",
  test_result: "Результат испытания",
  work_order: "Наряд-заказ",
  training_record: "Запись обучения",
  certificate: "Сертификат",
  measurement: "Измерение",
  approval: "Согласование",
  other: "Иное",
};

const VERIFICATION_TYPE_LABELS: Record<VerificationTypeDto, string> = {
  initial: "Первичная",
  scheduled_review: "Плановый пересмотр",
  post_incident: "После инцидента",
  post_inspection: "После проверки",
  post_change: "После изменения",
  management_review: "Анализ руководства",
  other: "Иная",
};

const REVIEW_BASIS_LABELS: Record<ReviewBasisDto, string> = {
  fixed_interval: "Фиксированный интервал",
  risk_based: "На основе риска",
  regulatory_requirement: "Требование НПА",
  manufacturer_requirement: "Требование изготовителя",
  corporate_policy: "Корпоративная политика",
  post_incident: "После инцидента",
  post_change: "После изменения",
  manual: "Вручную",
};

const OWNER_TYPE_LABELS: Record<OwnerTypeDto, string> = {
  user: "Пользователь",
  employee: "Работник",
  role: "Роль",
  organizational_unit: "Подразделение",
  external_party: "Внешняя сторона",
};

const MILESTONE_STATUS_LABELS: Record<MilestoneStatusDto, string> = {
  pending: "Ожидает",
  in_progress: "В работе",
  completed: "Выполнено",
  blocked: "Заблокировано",
  cancelled: "Отменено",
};

const ENUM_LABEL_LOOKUP: Record<string, string> = {
  ...HIERARCHY_LEVEL_LABELS,
  ...CONTROL_NATURE_LABELS,
  ...EVIDENCE_TYPE_LABELS,
  ...VERIFICATION_TYPE_LABELS,
  ...REVIEW_BASIS_LABELS,
  ...OWNER_TYPE_LABELS,
  ...MILESTONE_STATUS_LABELS,
};

/** Unknown wire values pass through unchanged. */
export function formatRiskControlEnumLabel(value: string): string {
  return ENUM_LABEL_LOOKUP[value] ?? value;
}

export function hierarchyLevelLabel(value: string): string {
  return HIERARCHY_LEVEL_LABELS[value as ControlTypeDto] ?? value;
}

export function controlNatureLabel(value: string): string {
  return CONTROL_NATURE_LABELS[value as ControlNatureDto] ?? value;
}

export function evidenceTypeLabel(value: string): string {
  return EVIDENCE_TYPE_LABELS[value as EvidenceTypeDto] ?? value;
}

export function verificationTypeLabel(value: string): string {
  return VERIFICATION_TYPE_LABELS[value as VerificationTypeDto] ?? value;
}

export function reviewBasisLabel(value: string): string {
  return REVIEW_BASIS_LABELS[value as ReviewBasisDto] ?? value;
}

export function ownerTypeLabel(value: string): string {
  return OWNER_TYPE_LABELS[value as OwnerTypeDto] ?? value;
}

export function milestoneStatusLabel(value: string): string {
  return MILESTONE_STATUS_LABELS[value as MilestoneStatusDto] ?? value;
}

export function riskControlStatusToVisual(
  status: RiskControlStatusDto,
): VisualStatus {
  return STATUS_TO_VISUAL[status];
}

export function riskControlStatusLabel(status: RiskControlStatusDto): string {
  return STATUS_LABELS[status];
}

/** Null when nothing has been verified yet — callers render text, not a badge. */
export function effectivenessToVisual(
  result: string | null | undefined,
): VisualStatus | null {
  if (!result) {
    return null;
  }
  return EFFECTIVENESS_TO_VISUAL[result] ?? null;
}

export function effectivenessLabel(result: string | null | undefined): string {
  if (!result) {
    return "Не подтверждена";
  }
  return EFFECTIVENESS_LABELS[result] ?? result;
}

/** Implementation is a separate dimension from lifecycle status. */
export function implementationStateLabel(input: {
  status: RiskControlStatusDto;
  progress: number;
  actualCompletionDate: string | null;
}): string {
  if (input.actualCompletionDate) {
    return "Внедрено";
  }
  switch (input.status) {
    case "draft":
      return "Не запланировано";
    case "planned":
      return "Запланировано";
    case "in_implementation":
      return `В работе — ${input.progress}%`;
    case "implemented":
    case "verified_effective":
    case "verified_ineffective":
      return "Внедрено";
    default:
      return input.progress > 0 ? `В работе — ${input.progress}%` : "Не начато";
  }
}
