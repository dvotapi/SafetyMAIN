import type { VisualStatus } from "@/components";

import type {
  AffectedSubjectDto,
  HazardCategoryDto,
  HazardSourceDto,
  HazardStatusDto,
  SafetyDirectionDto,
} from "@/features/hazards/types/hazard-types";

const STATUS_TO_VISUAL: Record<HazardStatusDto, VisualStatus> = {
  draft: "draft",
  active: "active",
  archived: "archived",
};

const STATUS_LABELS: Record<HazardStatusDto, string> = {
  draft: "Черновик",
  active: "Действует",
  archived: "Архив",
};

const CATEGORY_LABELS: Record<HazardCategoryDto, string> = {
  physical: "Физическая",
  mechanical: "Механическая",
  electrical: "Электрическая",
  chemical: "Химическая",
  biological: "Биологическая",
  ergonomic: "Эргономическая",
  psychosocial: "Психосоциальная",
  fire_and_explosion: "Пожар и взрыв",
  thermal: "Тепловая",
  radiation: "Радиационная",
  pressure: "Давление",
  work_at_height: "Работа на высоте",
  confined_space: "Замкнутое пространство",
  transport: "Транспортная",
  environmental: "Экологическая",
  dangerous_goods: "Опасные грузы",
  process_safety: "Безопасность процессов",
  natural_hazard: "Природная опасность",
  organizational: "Организационная",
  other: "Иная",
};

const SAFETY_DIRECTION_LABELS: Record<SafetyDirectionDto, string> = {
  occupational_safety: "Охрана труда",
  industrial_safety: "Промышленная безопасность",
  fire_safety: "Пожарная безопасность",
  environmental_safety: "Экологическая безопасность",
  transport_safety: "Транспортная безопасность",
  dangerous_goods_transport: "Перевозка опасных грузов",
  civil_defense_and_emergency: "ГО и ЧС",
  sanitary_and_hygienic_safety: "Санитарно-гигиеническая безопасность",
  electrical_safety: "Электробезопасность",
  radiation_safety: "Радиационная безопасность",
};

const SOURCE_LABELS: Record<HazardSourceDto, string> = {
  employee_report: "Сообщение работника",
  inspection: "Проверка",
  incident_investigation: "Расследование инцидента",
  near_miss: "Опасное событие без последствий",
  risk_assessment: "Оценка риска",
  regulatory_assessment: "Регуляторная оценка",
  audit: "Аудит",
  management_review: "Анализ со стороны руководства",
  change_management: "Управление изменениями",
  equipment_documentation: "Документация на оборудование",
  sout: "СОУТ",
  production_control: "Производственный контроль",
  environmental_monitoring: "Экологический мониторинг",
  transport_control: "Транспортный контроль",
  other: "Иной",
};

const AFFECTED_SUBJECT_LABELS: Record<AffectedSubjectDto, string> = {
  employee: "Работник",
  contractor: "Подрядчик",
  visitor: "Посетитель",
  driver: "Водитель",
  passenger: "Пассажир",
  public: "Третьи лица",
  environment: "Окружающая среда",
  equipment: "Оборудование",
  building: "Здание",
  transport_vehicle: "Транспортное средство",
  cargo: "Груз",
  production_process: "Производственный процесс",
};

/** Related RA rows on the hazard object page (Phase C owns full RA maps). */
const RELATED_ASSESSMENT_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  under_review: "На рассмотрении",
  approved: "Утверждено",
  superseded: "Замещено",
  archived: "Архив",
};

const ASSESSMENT_PROFILE_LABELS: Record<string, string> = {
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

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  extreme: "Крайний",
};

export function hazardStatusToVisual(status: HazardStatusDto): VisualStatus {
  return STATUS_TO_VISUAL[status];
}

export function hazardStatusLabel(status: HazardStatusDto): string {
  return STATUS_LABELS[status];
}

export function hazardCategoryLabel(value: HazardCategoryDto): string {
  return CATEGORY_LABELS[value];
}

export function safetyDirectionLabel(value: SafetyDirectionDto): string {
  return SAFETY_DIRECTION_LABELS[value];
}

export function hazardSourceLabel(value: HazardSourceDto): string {
  return SOURCE_LABELS[value];
}

export function affectedSubjectLabel(value: AffectedSubjectDto): string {
  return AFFECTED_SUBJECT_LABELS[value];
}

export function relatedAssessmentStatusLabel(value: string): string {
  return RELATED_ASSESSMENT_STATUS_LABELS[value] ?? value;
}

export function assessmentProfileLabel(value: string): string {
  return ASSESSMENT_PROFILE_LABELS[value] ?? value;
}

export function riskLevelLabel(value: string): string {
  const key = value.trim().toLowerCase();
  return RISK_LEVEL_LABELS[key] ?? value;
}
