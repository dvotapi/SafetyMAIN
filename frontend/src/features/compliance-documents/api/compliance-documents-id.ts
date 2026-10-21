const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Guard every path segment that comes from the URL (Next.js dynamic
 * route param). The backend already rejects malformed ids with 422, but
 * refusing to issue a request with a non-UUID keeps a `../` or ` %2F`
 * from ever leaving the client — defence against client-side path
 * traversal (CSPT). Encoded on top in case a well-formed UUID is extended
 * by weird input in the future.
 */
export function assertComplianceDocumentId(documentId: string): string {
  if (!UUID_RE.test(documentId)) {
    throw new Error("Invalid compliance document id");
  }
  return encodeURIComponent(documentId);
}
