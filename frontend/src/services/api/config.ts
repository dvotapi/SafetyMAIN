import { getPublicEnv } from "@/lib/env";

export interface ApiClientConfig {
  baseUrl: string;
  defaultHeaders?: Record<string, string>;
}

export function createApiClientConfig(
  overrides: Partial<ApiClientConfig> = {},
): ApiClientConfig {
  const env = getPublicEnv();
  return {
    baseUrl:
      overrides.baseUrl ?? env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, ""),
    defaultHeaders: {
      Accept: "application/json",
      ...overrides.defaultHeaders,
    },
  };
}
