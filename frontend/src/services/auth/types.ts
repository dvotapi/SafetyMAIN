/**
 * Auth service extension points (TASK-P9-004).
 * Do not persist tokens insecurely by default.
 */
export type AccessTokenProvider = () => string | null | Promise<string | null>;
export type OrganizationIdProvider = () =>
  string | null | Promise<string | null>;
