/**
 * Filter chips of TASK-P11-012 §4.3.1. They only dim places by DTO fields;
 * nothing is removed, so the shelf keeps its shape.
 */
import type {
  ShelfSlotSummaryDto,
  ShelfStatusGroup,
} from "@/features/document-shelf/types/shelf-dto";
import type { ShelfFilter } from "@/features/document-shelf/utils/shelf-url-state";

const PROBLEM_GROUPS: ReadonlySet<ShelfStatusGroup> = new Set([
  "missing",
  "review",
]);

export function stripItemMatches(
  group: ShelfStatusGroup,
  filter: ShelfFilter,
): boolean {
  if (filter === "problems") return PROBLEM_GROUPS.has(group);
  // The overview strip has no obligation level; «Обязательные» dims only excluded bars.
  if (filter === "mandatory") return group !== "excluded";
  return true;
}

export function slotMatches(
  slot: ShelfSlotSummaryDto,
  filter: ShelfFilter,
): boolean {
  if (filter === "problems") {
    return PROBLEM_GROUPS.has(slot.group) || slot.has_acknowledgement_gap;
  }
  if (filter === "mandatory") {
    return slot.obligation_level === "mandatory" && slot.group !== "excluded";
  }
  return true;
}
