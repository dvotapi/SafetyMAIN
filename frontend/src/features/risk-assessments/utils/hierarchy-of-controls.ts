import type { ControlTypeDto } from "@/features/risk-assessments/types/risk-assessment-types";

/** Hierarchy of Controls — most preferred first (matches backend ranks). */
export const HIERARCHY_OF_CONTROLS: readonly ControlTypeDto[] = [
  "elimination",
  "substitution",
  "engineering",
  "administrative",
  "ppe",
] as const;

const RANK: Record<ControlTypeDto, number> = {
  elimination: 1,
  substitution: 2,
  engineering: 3,
  administrative: 4,
  ppe: 5,
};

export function hierarchyRank(controlType: ControlTypeDto): number {
  return RANK[controlType];
}

export function isHigherOnHierarchy(
  left: ControlTypeDto,
  right: ControlTypeDto,
): boolean {
  return hierarchyRank(left) < hierarchyRank(right);
}

export function sortControlsByHierarchy<
  T extends { controlType: ControlTypeDto },
>(controls: readonly T[]): T[] {
  return [...controls].sort(
    (a, b) => hierarchyRank(a.controlType) - hierarchyRank(b.controlType),
  );
}

export function controlTypeLabel(controlType: ControlTypeDto): string {
  const labels: Record<ControlTypeDto, string> = {
    elimination: "Устранение",
    substitution: "Замена",
    engineering: "Инженерные меры",
    administrative: "Административные меры",
    ppe: "СИЗ",
  };
  return labels[controlType];
}
