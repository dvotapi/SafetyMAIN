import {
  createApiClientConfig,
  type ApiClientConfig,
} from "@/services/api/config";
import { normalizeApiError } from "@/services/api/errors";
import type { ApiRequestOptions } from "@/services/api/types";

function buildUrl(
  baseUrl: string,
  path: string,
  query?: ApiRequestOptions["query"],
): string {
  const url = new URL(
    path.startsWith("http")
      ? path
      : `${baseUrl}${path.startsWith("/") ? "" : "/"}${path}`,
  );
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null) {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export class ApiClient {
  private readonly config: ApiClientConfig;

  constructor(config: ApiClientConfig = createApiClientConfig()) {
    this.config = config;
  }

  async request<T>(options: ApiRequestOptions): Promise<T | null> {
    const method = options.method ?? "GET";
    const correlationId =
      options.correlationId ??
      (typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `req-${Date.now()}`);

    const headers: Record<string, string> = {
      ...this.config.defaultHeaders,
      ...options.headers,
      "X-Request-Id": correlationId,
    };

    const token = options.getAccessToken
      ? await options.getAccessToken()
      : null;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const organizationId = options.getOrganizationId
      ? await options.getOrganizationId()
      : null;
    if (organizationId) {
      headers["X-Organization-Id"] = organizationId;
    }

    let response: Response;
    try {
      const init: RequestInit = {
        method,
        headers,
      };
      if (options.body !== undefined) {
        headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(options.body);
      }
      if (options.signal) {
        init.signal = options.signal;
      }
      response = await fetch(
        buildUrl(this.config.baseUrl, options.path, options.query),
        init,
      );
    } catch (cause) {
      throw normalizeApiError({
        status: null,
        body: null,
        fallbackMessage: "Network request failed",
        correlationId,
        cause,
      });
    }

    if (response.status === 204) {
      return null;
    }

    const text = await response.text();
    let parsed: unknown = null;
    if (text) {
      try {
        parsed = JSON.parse(text) as unknown;
      } catch {
        parsed = { message: text };
      }
    }

    if (!response.ok) {
      throw normalizeApiError({
        status: response.status,
        body: parsed,
        correlationId,
      });
    }

    return parsed as T;
  }
}

export const apiClient = new ApiClient();
