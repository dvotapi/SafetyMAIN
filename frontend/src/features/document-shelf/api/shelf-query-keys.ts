export const shelfKeys = {
  all: (organizationId: string | null) =>
    ["document-shelf", organizationId ?? "none"] as const,
  overview: (organizationId: string | null) =>
    [...shelfKeys.all(organizationId), "overview"] as const,
  section: (organizationId: string | null, sectionCode: string) =>
    [...shelfKeys.all(organizationId), "section", sectionCode] as const,
  slot: (organizationId: string | null, slotId: string) =>
    [...shelfKeys.all(organizationId), "slot", slotId] as const,
  search: (organizationId: string | null, query: string) =>
    [...shelfKeys.all(organizationId), "search", query] as const,
};
