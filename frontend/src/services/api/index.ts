export { apiClient, ApiClient } from "@/services/api/client";
export { createApiClientConfig } from "@/services/api/config";
export {
  ApiClientError,
  AuthenticationError,
  ConflictError,
  NetworkError,
  NotFoundError,
  PermissionError,
  TenantContextError,
  UnexpectedApiError,
  ValidationError,
  normalizeApiError,
  toUserSafeMessage,
} from "@/services/api/errors";
