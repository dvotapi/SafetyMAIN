import type {
  AccessTokenProvider,
  OrganizationIdProvider,
} from "@/services/auth/types";

export type UnauthorizedHandler = () => Promise<boolean>;

interface AuthBridge {
  getAccessToken: AccessTokenProvider;
  getOrganizationId: OrganizationIdProvider;
  onUnauthorized: UnauthorizedHandler;
}

let bridge: AuthBridge | null = null;

export function bindAuthProviders(next: AuthBridge): void {
  bridge = next;
}

export function clearAuthProviders(): void {
  bridge = null;
}

export function getBoundAccessToken(): ReturnType<AccessTokenProvider> {
  return bridge?.getAccessToken() ?? null;
}

export function getBoundOrganizationId(): ReturnType<OrganizationIdProvider> {
  return bridge?.getOrganizationId() ?? null;
}

export async function notifyUnauthorized(): Promise<boolean> {
  if (!bridge) {
    return false;
  }
  return bridge.onUnauthorized();
}
