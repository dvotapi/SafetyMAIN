import { apiClient } from "@/services/api/client";

import {
  shelfOverviewSchema,
  shelfSectionSlotsSchema,
  shelfSlotDetailSchema,
  shelfSlotListSchema,
} from "@/features/document-shelf/schemas/shelf-response-schemas";
import type {
  ShelfOverviewDto,
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
