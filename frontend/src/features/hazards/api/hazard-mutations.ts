"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  activateHazard,
  archiveHazard,
  createHazard,
  restoreHazard,
  updateHazard,
} from "@/features/hazards/api/hazard-api";
import { hazardKeys } from "@/features/hazards/api/hazard-query-keys";
import type {
  CreateHazardDto,
  UpdateHazardDto,
} from "@/features/hazards/types/hazard-types";
import { useOrganization } from "@/hooks/auth";

function useInvalidateHazards() {
  const queryClient = useQueryClient();
  const { organizationId } = useOrganization();
  return {
    queryClient,
    organizationId,
    invalidateLists: () =>
      queryClient.invalidateQueries({
        queryKey: hazardKeys.lists(organizationId),
      }),
    setDetail: (hazardId: string, data: unknown) =>
      queryClient.setQueryData(
        hazardKeys.detail(organizationId, hazardId),
        data,
      ),
    invalidateDetail: (hazardId: string) =>
      queryClient.invalidateQueries({
        queryKey: hazardKeys.detail(organizationId, hazardId),
      }),
  };
}

export function useCreateHazardMutation() {
  const { invalidateLists, setDetail } = useInvalidateHazards();
  return useMutation({
    mutationFn: (body: CreateHazardDto) => createHazard(body),
    onSuccess: (hazard) => {
      setDetail(hazard.id, hazard);
      void invalidateLists();
    },
  });
}

export function useUpdateHazardMutation(hazardId: string) {
  const { invalidateLists, setDetail, invalidateDetail } =
    useInvalidateHazards();
  return useMutation({
    mutationFn: (body: UpdateHazardDto) => updateHazard(hazardId, body),
    onSuccess: (hazard) => {
      setDetail(hazard.id, hazard);
      void invalidateLists();
      void invalidateDetail(hazard.id);
    },
  });
}

export function useActivateHazardMutation(hazardId: string) {
  const { invalidateLists, setDetail, invalidateDetail } =
    useInvalidateHazards();
  return useMutation({
    mutationFn: (expectedVersion: number) =>
      activateHazard(hazardId, expectedVersion),
    onSuccess: (hazard) => {
      setDetail(hazard.id, hazard);
      void invalidateLists();
      void invalidateDetail(hazard.id);
    },
  });
}

export function useArchiveHazardMutation(hazardId: string) {
  const { invalidateLists, setDetail, invalidateDetail } =
    useInvalidateHazards();
  return useMutation({
    mutationFn: ({
      expectedVersion,
      reason,
    }: {
      expectedVersion: number;
      reason: string;
    }) => archiveHazard(hazardId, expectedVersion, reason),
    onSuccess: (hazard) => {
      setDetail(hazard.id, hazard);
      void invalidateLists();
      void invalidateDetail(hazard.id);
    },
  });
}

export function useRestoreHazardMutation(hazardId: string) {
  const { invalidateLists, setDetail, invalidateDetail } =
    useInvalidateHazards();
  return useMutation({
    mutationFn: ({
      expectedVersion,
      reason,
    }: {
      expectedVersion: number;
      reason: string;
    }) => restoreHazard(hazardId, expectedVersion, reason),
    onSuccess: (hazard) => {
      setDetail(hazard.id, hazard);
      void invalidateLists();
      void invalidateDetail(hazard.id);
    },
  });
}
