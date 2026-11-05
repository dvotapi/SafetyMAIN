/**
 * URL state of the shelf page (TASK-P11-012 §4.2):
 * `?section=ТрБ&slot=ТрБ.02.02&filter=problems&excluded=hidden`.
 * Unknown values fall back to the defaults, so a shared link never breaks.
 */

export const SHELF_FILTERS = ["all", "problems", "mandatory"] as const;
export type ShelfFilter = (typeof SHELF_FILTERS)[number];

export interface ShelfUrlState {
  section: string | null;
  slot: string | null;
  filter: ShelfFilter;
  excludedHidden: boolean;
}

export const DEFAULT_SHELF_URL_STATE: ShelfUrlState = {
  section: null,
  slot: null,
  filter: "all",
  excludedHidden: false,
};

const SECTION_CODE = /^[А-ЯЁа-яё]{2,6}$/;
const SLOT_CODE = /^[А-ЯЁа-яё]+\.\d{2}\.\d{2}$/;

export function parseShelfUrlState(params: URLSearchParams): ShelfUrlState {
  const section = params.get("section");
  const slot = params.get("slot");
  const filter = params.get("filter");
  const validSection = section && SECTION_CODE.test(section) ? section : null;
  const validSlot =
    validSection &&
    slot &&
    SLOT_CODE.test(slot) &&
    slot.startsWith(`${validSection}.`)
      ? slot
      : null;
  return {
    section: validSection,
    slot: validSlot,
    filter: (SHELF_FILTERS as readonly string[]).includes(filter ?? "")
      ? (filter as ShelfFilter)
      : "all",
    excludedHidden: params.get("excluded") === "hidden",
  };
}

export function serializeShelfUrlState(state: ShelfUrlState): string {
  const params = new URLSearchParams();
  if (state.section) params.set("section", state.section);
  if (state.section && state.slot) params.set("slot", state.slot);
  if (state.filter !== "all") params.set("filter", state.filter);
  if (state.excludedHidden) params.set("excluded", "hidden");
  return params.toString();
}
