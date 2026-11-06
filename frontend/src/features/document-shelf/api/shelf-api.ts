import { apiClient } from "@/services/api/client";

import {
  developShelfSlotSchema,
  shelfDocumentPageSchema,
  shelfDocumentRefSchema,
  shelfDocumentTypesSchema,
  shelfFileUrlSchema,
  shelfOverviewSchema,
  shelfSectionSlotsSchema,
  shelfSlotDetailSchema,
  shelfSlotListSchema,
} from "@/features/document-shelf/schemas/shelf-response-schemas";
import type {
  DevelopShelfSlotDto,
  ShelfDocumentRefDto,
  ShelfDocumentTypesDto,
  ShelfFileUrlDto,
  ShelfOverviewDto,
  SlotExclusionReason,
  ShelfSectionSlotsDto,
  ShelfSlotDetailDto,
  ShelfSlotListDto,
} from "@/features/document-shelf/types/shelf-dto";

const BASE_PATH = "/api/v1/shelf";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function requireBody<T>(value: T | null, label: string): T {
  if (value === null || value === undefined) {
    throw new Error(`Empty ${label} response`);
  }
  return value;
}

function withSignal(signal?: AbortSignal) {
  return signal ? { signal } : {};
}

export async function getShelfOverview(
  signal?: AbortSignal,
): Promise<ShelfOverviewDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: BASE_PATH,
    ...withSignal(signal),
  });
  return shelfOverviewSchema.parse(requireBody(dto, "shelf overview"));
}

export async function getShelfSectionSlots(
  sectionCode: string,
  signal?: AbortSignal,
): Promise<ShelfSectionSlotsDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/sections/${encodeURIComponent(sectionCode)}/slots`,
    ...withSignal(signal),
  });
  return shelfSectionSlotsSchema.parse(requireBody(dto, "shelf section"));
}

export async function searchShelfSlots(
  query: string,
  limit = 20,
  signal?: AbortSignal,
): Promise<ShelfSlotListDto> {
  const search = new URLSearchParams({ q: query, limit: String(limit) });
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/slots?${search.toString()}`,
    ...withSignal(signal),
  });
  return shelfSlotListSchema.parse(requireBody(dto, "shelf search"));
}

export async function getShelfSlot(
  slotId: string,
  signal?: AbortSignal,
): Promise<ShelfSlotDetailDto> {
  if (!UUID.test(slotId)) throw new Error("Invalid shelf place id");
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${BASE_PATH}/slots/${slotId}`,
    ...withSignal(signal),
  });
  return shelfSlotDetailSchema.parse(requireBody(dto, "shelf place"));
}

// ---- place commands (curator) ----

function assertUuid(value: string, label: string): string {
  if (!UUID.test(value)) throw new Error(`Invalid ${label} id`);
  return value;
}

async function postSlot(
  slotId: string,
  suffix: string,
  body: unknown,
): Promise<ShelfSlotDetailDto> {
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path: `${BASE_PATH}/slots/${assertUuid(slotId, "shelf place")}/${suffix}`,
    body,
  });
  return shelfSlotDetailSchema.parse(requireBody(dto, `shelf ${suffix}`));
}

export function excludeShelfSlot(
  slotId: string,
  body: { reason: SlotExclusionReason; comment: string; version: number },
): Promise<ShelfSlotDetailDto> {
  return postSlot(slotId, "exclude", body);
}

export function restoreShelfSlot(slotId: string, version: number) {
  return postSlot(slotId, "restore", { version });
}

export function confirmShelfSlotApplicable(slotId: string, version: number) {
  return postSlot(slotId, "confirm-applicable", { version });
}

export function linkShelfSlotDocument(
  slotId: string,
  documentId: string,
  version: number,
) {
  return postSlot(slotId, "documents", { document_id: documentId, version });
}

export async function bulkExcludeShelfSlots(body: {
  items: Array<{ slot_id: string; version: number }>;
  reason: SlotExclusionReason;
  comment: string;
}): Promise<ShelfSlotListDto> {
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path: `${BASE_PATH}/slots/bulk-exclude`,
    body,
  });
  return shelfSlotListSchema.parse(requireBody(dto, "shelf bulk exclude"));
}

export async function developShelfSlot(
  slotId: string,
  body: { version: number; document_type_code?: string },
): Promise<DevelopShelfSlotDto> {
  const dto = await apiClient.request<unknown>({
    method: "POST",
    path: `${BASE_PATH}/slots/${assertUuid(slotId, "shelf place")}/develop`,
    body,
  });
  return developShelfSlotSchema.parse(requireBody(dto, "shelf develop"));
}

// ---- documented compliance endpoints the shelf reads (TASK §4.2) ----

const DOCUMENTS_PATH = "/api/v1/compliance-documents";

export async function getShelfDocument(
  documentId: string,
  signal?: AbortSignal,
): Promise<ShelfDocumentRefDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${DOCUMENTS_PATH}/${assertUuid(documentId, "document")}`,
    ...withSignal(signal),
  });
  return shelfDocumentRefSchema.parse(requireBody(dto, "document"));
}

export async function searchOrganizationDocuments(
  search: string,
  signal?: AbortSignal,
): Promise<ShelfDocumentRefDto[]> {
  const query = new URLSearchParams({
    search,
    subject_kind: "organization",
    limit: "10",
  });
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${DOCUMENTS_PATH}?${query.toString()}`,
    ...withSignal(signal),
  });
  return shelfDocumentPageSchema.parse(requireBody(dto, "documents")).items;
}

export async function getFileViewUrl(
  documentId: string,
  fileId: string,
  signal?: AbortSignal,
): Promise<ShelfFileUrlDto> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${DOCUMENTS_PATH}/${assertUuid(documentId, "document")}/files/${assertUuid(fileId, "file")}/view-url`,
    ...withSignal(signal),
  });
  return shelfFileUrlSchema.parse(requireBody(dto, "view url"));
}

export async function getFileDownloadUrl(
  documentId: string,
  kind: "working" | "signed_scan",
): Promise<ShelfFileUrlDto> {
  const suffix =
    kind === "signed_scan"
      ? "files/signed-scan/current/download-url"
      : "files/current/download-url";
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: `${DOCUMENTS_PATH}/${assertUuid(documentId, "document")}/${suffix}`,
  });
  return shelfFileUrlSchema.parse(requireBody(dto, "download url"));
}

export async function listActiveDocumentTypes(
  signal?: AbortSignal,
): Promise<ShelfDocumentTypesDto["items"]> {
  const dto = await apiClient.request<unknown>({
    method: "GET",
    path: "/api/v1/document-types",
    ...withSignal(signal),
  });
  return shelfDocumentTypesSchema
    .parse(requireBody(dto, "document types"))
    .items.filter(
      (item) => item.is_active && item.subject_kind === "organization",
    );
}
