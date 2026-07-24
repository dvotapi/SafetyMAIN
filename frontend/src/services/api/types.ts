export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type ApiErrorKind =
  | "validation"
  | "authentication"
  | "permission"
  | "not_found"
  | "conflict"
  | "tenant_context"
  | "network"
  | "unexpected";

export interface ApiRequestOptions {
  method?: HttpMethod;
  path: string;
  query?: Record<string, string | number | boolean | undefined | null>;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  /** Extension point — do not persist tokens insecurely by default. */
  getAccessToken?: () => string | null | Promise<string | null>;
  /** Extension point for TenantContext / org header. */
  getOrganizationId?: () => string | null | Promise<string | null>;
  correlationId?: string;
}

export interface ApiErrorBody {
  code?: string;
  message?: string;
  details?: unknown;
  correlation_id?: string;
}

export interface ApiError {
  kind: ApiErrorKind;
  status: number | null;
  message: string;
  code?: string;
  details?: unknown;
  correlationId?: string;
  cause?: unknown;
}
