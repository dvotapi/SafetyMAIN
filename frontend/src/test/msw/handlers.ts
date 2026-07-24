/**
 * MSW is for local/dev/test only — never bundle into production app code paths.
 * Example handlers live here for future feature work.
 */
import { http, HttpResponse } from "msw";

export const bootstrapHandlers = [
  http.get("*/api/v1/health", () => HttpResponse.json({ status: "ok" })),
];
