/** Spine sizes of TASK-P11-012 §4.3.5 (lookups, no calculation). */

const WIDTH_BY_KIND: Record<string, number> = {
  Журнал: 30,
  "Проект / паспорт": 32,
  План: 30,
  "Карта / реестр": 28,
  Перечень: 28,
  Положение: 28,
  "Порядок / процедура": 26,
  Инструкция: 26,
  Программа: 26,
  Политика: 26,
  Отчёт: 24,
  Акт: 24,
  Протокол: 24,
  "Договор / полис": 24,
  Приказ: 22,
  "Удостоверение / свидетельство": 22,
  "Разрешение / лицензия": 22,
};

const HEIGHT_BY_OBLIGATION: Record<string, number> = {
  mandatory: 136,
  conditional: 114,
  recommended: 98,
};

export const DEFAULT_SPINE_WIDTH = 24;
export const EXCLUDED_SPINE = { width: 12, height: 70 } as const;

export function spineSize(
  documentKind: string,
  obligationLevel: string,
  excluded: boolean,
): { width: number; height: number } {
  if (excluded) return EXCLUDED_SPINE;
  return {
    width: WIDTH_BY_KIND[documentKind] ?? DEFAULT_SPINE_WIDTH,
    height:
      HEIGHT_BY_OBLIGATION[obligationLevel] ??
      HEIGHT_BY_OBLIGATION.recommended!,
  };
}
