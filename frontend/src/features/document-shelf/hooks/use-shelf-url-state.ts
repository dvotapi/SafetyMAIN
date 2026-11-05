"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import {
  parseShelfUrlState,
  serializeShelfUrlState,
  type ShelfUrlState,
} from "@/features/document-shelf/utils/shelf-url-state";

/**
 * Opening a section or a place pushes a history entry (back/forward work);
 * filters and the excluded toggle replace it.
 */
export function useShelfUrlState() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const state = useMemo(
    () => parseShelfUrlState(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );

  const navigate = useCallback(
    (next: ShelfUrlState, mode: "push" | "replace") => {
      const query = serializeShelfUrlState(next);
      const href = query ? `${pathname}?${query}` : pathname;
      if (mode === "push") router.push(href, { scroll: false });
      else router.replace(href, { scroll: false });
    },
    [pathname, router],
  );

  const openSection = useCallback(
    (section: string | null, slot: string | null = null) =>
      navigate({ ...state, section, slot }, "push"),
    [navigate, state],
  );
  const selectSlot = useCallback(
    (slot: string | null) => navigate({ ...state, slot }, "push"),
    [navigate, state],
  );
  const setFilter = useCallback(
    (filter: ShelfUrlState["filter"]) =>
      navigate({ ...state, filter }, "replace"),
    [navigate, state],
  );
  const setExcludedHidden = useCallback(
    (excludedHidden: boolean) =>
      navigate({ ...state, excludedHidden }, "replace"),
    [navigate, state],
  );

  return { state, openSection, selectSlot, setFilter, setExcludedHidden };
}
