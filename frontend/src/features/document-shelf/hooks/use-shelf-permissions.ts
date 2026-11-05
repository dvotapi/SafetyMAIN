"use client";

import { useAuth } from "@/hooks/auth";

export interface ShelfCapabilities {
  canRead: boolean;
  /** Only gates UI chrome (selection mode); place actions come from the API. */
  canCurate: boolean;
}

export function mapShelfCapabilities(
  hasPermission: (permission: string) => boolean,
): ShelfCapabilities {
  return {
    canRead: hasPermission("shelf:read"),
    canCurate: hasPermission("shelf:curate"),
  };
}

export function useShelfPermissions(): ShelfCapabilities {
  const { hasPermission } = useAuth();
  return mapShelfCapabilities(hasPermission);
}
