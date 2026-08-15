export function useRouter() {
  return {
    push: () => undefined,
    replace: () => undefined,
    prefetch: () => undefined,
    back: () => undefined,
    forward: () => undefined,
    refresh: () => undefined,
  };
}

export function usePathname() {
  return "/login";
}

export function useSearchParams() {
  return new URLSearchParams();
}

export function useParams() {
  return {};
}
