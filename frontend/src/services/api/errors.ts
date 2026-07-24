import type { ApiError, ApiErrorKind } from "@/services/api/types";

export class ApiClientError extends Error implements ApiError {
  readonly kind: ApiErrorKind;
  readonly status: number | null;
  readonly code?: string;
  readonly details?: unknown;
  readonly correlationId?: string;
  override readonly cause?: unknown;

  constructor(error: ApiError) {
    super(error.message);
    this.name = "ApiClientError";
    this.kind = error.kind;
    this.status = error.status;
    if (error.code !== undefined) {
      this.code = error.code;
    }
    if (error.details !== undefined) {
      this.details = error.details;
    }
    if (error.correlationId !== undefined) {
      this.correlationId = error.correlationId;
    }
    if (error.cause !== undefined) {
      this.cause = error.cause;
    }
  }
}

export class ValidationError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "validation" });
    this.name = "ValidationError";
  }
}

export class AuthenticationError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "authentication" });
    this.name = "AuthenticationError";
  }
}

export class PermissionError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "permission" });
    this.name = "PermissionError";
  }
}

export class NotFoundError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "not_found" });
    this.name = "NotFoundError";
  }
}

export class ConflictError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "conflict" });
    this.name = "ConflictError";
  }
}

export class TenantContextError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "tenant_context" });
    this.name = "TenantContextError";
  }
}

export class NetworkError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind" | "status"> & { status?: null }) {
    super({ ...error, kind: "network", status: error.status ?? null });
    this.name = "NetworkError";
  }
}

export class UnexpectedApiError extends ApiClientError {
  constructor(error: Omit<ApiError, "kind">) {
    super({ ...error, kind: "unexpected" });
    this.name = "UnexpectedApiError";
  }
}

interface NormalizeInput {
  status: number | null;
  body: unknown;
  fallbackMessage?: string;
  correlationId?: string;
  cause?: unknown;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function readString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

/** Normalize backend/network failures into UI-safe error types. */
export function normalizeApiError(input: NormalizeInput): ApiClientError {
  const record = asRecord(input.body);
  const code = readString(record?.["code"]);
  const message =
    readString(record?.["message"]) ??
    input.fallbackMessage ??
    "Unexpected API error";
  const details = record?.["details"] ?? record?.["errors"];
  const correlationId =
    input.correlationId ??
    readString(record?.["correlation_id"]) ??
    readString(record?.["correlationId"]);

  const base = {
    message,
    status: input.status,
    ...(code !== undefined ? { code } : {}),
    ...(details !== undefined ? { details } : {}),
    ...(correlationId !== undefined ? { correlationId } : {}),
    ...(input.cause !== undefined ? { cause: input.cause } : {}),
  };

  if (input.status === null) {
    return new NetworkError({
      message: base.message,
      ...(base.code !== undefined ? { code: base.code } : {}),
      ...(base.details !== undefined ? { details: base.details } : {}),
      ...(base.correlationId !== undefined
        ? { correlationId: base.correlationId }
        : {}),
      ...(base.cause !== undefined ? { cause: base.cause } : {}),
    });
  }
  if (input.status === 401) {
    return new AuthenticationError(base);
  }
  if (input.status === 403) {
    return new PermissionError(base);
  }
  if (input.status === 404) {
    return new NotFoundError(base);
  }
  if (input.status === 409) {
    return new ConflictError(base);
  }
  if (input.status === 422) {
    if (
      code === "organization_context_mismatch" ||
      code === "tenant_context_mismatch"
    ) {
      return new TenantContextError(base);
    }
    return new ValidationError(base);
  }
  return new UnexpectedApiError(base);
}

/** User-facing message without internal payloads. */
export function toUserSafeMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    switch (error.kind) {
      case "network":
        return "Network error. Check your connection and try again.";
      case "authentication":
        return "Authentication required.";
      case "permission":
        return "You do not have permission to perform this action.";
      case "not_found":
        return "The requested resource was not found.";
      case "conflict":
        return "This record was updated elsewhere. Refresh and try again.";
      case "tenant_context":
        return "Organization context mismatch.";
      case "validation":
        return error.message || "Please correct the highlighted fields.";
      default:
        return "Something went wrong. Try again later.";
    }
  }
  return "Something went wrong. Try again later.";
}
