import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components";
import { ComplianceDocumentUploadDialog } from "@/features/compliance-documents/components/compliance-document-upload-dialog";
import type { ComplianceDocumentDto } from "@/features/compliance-documents/types/compliance-documents-dto";
import { apiClient } from "@/services/api/client";
import type { ApiRequestOptions } from "@/services/api/types";

// jsdom's Blob lacks arrayBuffer(); polyfill via FileReader (jsdom supports it).
if (typeof Blob !== "undefined" && !("arrayBuffer" in Blob.prototype)) {
  Object.defineProperty(Blob.prototype, "arrayBuffer", {
    configurable: true,
    writable: true,
    value: function arrayBuffer(this: Blob) {
      return new Promise<ArrayBuffer>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as ArrayBuffer);
        reader.onerror = () => reject(reader.error);
        reader.readAsArrayBuffer(this);
      });
    },
  });
}

vi.mock("@/hooks/auth", () => ({
  useAuth: () => ({ hasPermission: () => true }),
  useOrganization: () => ({
    organizationId: "org-1",
    organizationName: "Org",
    membership: null,
  }),
}));

afterEach(cleanup);

const DOCUMENT_ID = "11111111-1111-1111-1111-111111111111";
const ORG_ID = "22222222-2222-2222-2222-222222222222";

function buildDocument(
  overrides: Partial<ComplianceDocumentDto> = {},
): ComplianceDocumentDto {
  return {
    id: DOCUMENT_ID,
    organization_id: ORG_ID,
    document_type_id: "33333333-3333-3333-3333-333333333333",
    subject_kind: "organization",
    subject_id: null,
    code: "CD-001",
    title: "Положение",
    status: "draft",
    issued_at: null,
    effective_from: null,
    next_review_at: null,
    approved_by_document_id: null,
    supersedes_document_id: null,
    superseded_by_document_id: null,
    applicability: {
      positions: [],
      work_types: [],
      departments: [],
      asset_ids: [],
    },
    source: "manual",
    current_file: null,
    notes: "",
    status_before_archive: null,
    archive_reason: null,
    is_review_due: false,
    created_at: "2026-10-01T00:00:00Z",
    created_by: "44444444-4444-4444-4444-444444444444",
    updated_at: "2026-10-01T00:00:00Z",
    updated_by: "44444444-4444-4444-4444-444444444444",
    version: 1,
    ...overrides,
  };
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const [queryClient] = [
    new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  ];
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  );
}

type RequestMock = ReturnType<typeof vi.spyOn>;

function installApiClientMock(
  impl: (options: ApiRequestOptions) => Promise<unknown>,
): RequestMock {
  return vi
    .spyOn(apiClient, "request")
    .mockImplementation(impl as never) as RequestMock;
}

// Minimal fake XHR capturing PUT body. We don't fire real network.
class FakeXhr {
  method = "";
  url = "";
  headers: Record<string, string> = {};
  body: unknown = null;
  status = 200;
  readonly upload = {
    onprogress: null as ((event: ProgressEvent) => void) | null,
  };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onabort: (() => void) | null = null;
  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }
  setRequestHeader(key: string, value: string) {
    this.headers[key] = value;
  }
  send(body: unknown) {
    this.body = body;
    if (this.upload.onprogress) {
      this.upload.onprogress({
        lengthComputable: true,
        loaded: 100,
        total: 100,
      } as ProgressEvent);
    }
    queueMicrotask(() => {
      if (this.status >= 200 && this.status < 300) this.onload?.();
      else this.onerror?.();
    });
  }
}

let lastXhr: FakeXhr | null = null;

beforeEach(() => {
  lastXhr = null;
  vi.stubGlobal(
    "XMLHttpRequest",
    class {
      private xhr = new FakeXhr();
      constructor() {
        lastXhr = this.xhr;
      }
      open(method: string, url: string) {
        this.xhr.open(method, url);
      }
      setRequestHeader(k: string, v: string) {
        this.xhr.setRequestHeader(k, v);
      }
      send(body: unknown) {
        this.xhr.send(body);
      }
      get upload() {
        return this.xhr.upload;
      }
      get status() {
        return this.xhr.status;
      }
      set onload(v: (() => void) | null) {
        this.xhr.onload = v;
      }
      set onerror(v: (() => void) | null) {
        this.xhr.onerror = v;
      }
      set onabort(v: (() => void) | null) {
        this.xhr.onabort = v;
      }
    },
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function fileFromBytes(name: string, type: string, bytes: Uint8Array) {
  // Cast via Blob to appease strict ArrayBuffer vs ArrayBufferLike typing.
  return new File([new Blob([bytes as BlobPart])], name, { type });
}

describe("ComplianceDocumentUploadDialog", () => {
  it("rejects a disallowed MIME type and never calls the API", async () => {
    const spy = installApiClientMock(() => Promise.resolve({}));
    render(
      <Wrapper>
        <ComplianceDocumentUploadDialog
          open
          onOpenChange={() => undefined}
          document={buildDocument()}
        />
      </Wrapper>,
    );
    const input = screen.getByTestId(
      "compliance-document-upload-input",
    ) as HTMLInputElement;
    const bad = await fileFromBytes(
      "evil.exe",
      "application/x-msdownload",
      new Uint8Array([1, 2, 3]),
    );
    // bypass accept-filter — browsers can be tricked via drag-drop or renames.
    fireEvent.change(input, { target: { files: [bad] } });
    await screen.findByText(/Недопустимый тип файла/i);
    expect(spy).not.toHaveBeenCalled();
  });

  it("rejects a file exceeding max size", async () => {
    const user = userEvent.setup();
    render(
      <Wrapper>
        <ComplianceDocumentUploadDialog
          open
          onOpenChange={() => undefined}
          document={buildDocument()}
          maxBytes={10}
        />
      </Wrapper>,
    );
    const input = screen.getByTestId(
      "compliance-document-upload-input",
    ) as HTMLInputElement;
    const big = await fileFromBytes(
      "big.pdf",
      "application/pdf",
      new Uint8Array(20),
    );
    await user.upload(input, big);
    expect(screen.getByText(/Файл слишком большой/i)).toBeInTheDocument();
  });

  it("walks happy path: hash → upload-url → PUT → confirm", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    const uploadUrlResponse = {
      upload_id: "u1",
      bucket: "b",
      key: "org-1/compliance_document/doc/u1/f.pdf",
      url: "https://example.test/signed",
      method: "PUT",
      headers: { "Content-Type": "application/pdf", "x-amz-meta-sha256": "x" },
      expires_at: "2030-01-01T00:00:00Z",
    };
    const confirmResponse = buildDocument({ version: 2 });
    const spy = installApiClientMock((options) => {
      if (options.path?.includes("/files/upload-url")) {
        return Promise.resolve(uploadUrlResponse);
      }
      if (options.path?.includes("/files/confirm")) {
        return Promise.resolve(confirmResponse);
      }
      return Promise.resolve(null);
    });

    render(
      <Wrapper>
        <ComplianceDocumentUploadDialog
          open
          onOpenChange={onOpenChange}
          document={buildDocument()}
        />
      </Wrapper>,
    );

    const input = screen.getByTestId(
      "compliance-document-upload-input",
    ) as HTMLInputElement;
    const file = await fileFromBytes(
      "briefing.pdf",
      "application/pdf",
      new Uint8Array([1, 2, 3, 4]),
    );
    await user.upload(input, file);
    await user.click(screen.getByRole("button", { name: "Загрузить" }));

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    const calls = spy.mock.calls.map((c) => (c[0] as ApiRequestOptions).path);
    expect(calls).toContain(
      `/api/v1/compliance-documents/${DOCUMENT_ID}/files/upload-url`,
    );
    expect(calls).toContain(
      `/api/v1/compliance-documents/${DOCUMENT_ID}/files/confirm`,
    );
    expect(lastXhr?.method).toBe("PUT");
    expect(lastXhr?.url).toBe("https://example.test/signed");
    expect(lastXhr?.headers["Content-Type"]).toBe("application/pdf");
  });

  it("surfaces a confirm error without closing the dialog", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    installApiClientMock((options) => {
      if (options.path?.includes("/files/upload-url")) {
        return Promise.resolve({
          upload_id: "u1",
          bucket: "b",
          key: "k",
          url: "https://example.test/signed",
          method: "PUT",
          headers: {},
          expires_at: "2030-01-01T00:00:00Z",
        });
      }
      if (options.path?.includes("/files/confirm")) {
        return Promise.reject(new Error("boom"));
      }
      return Promise.resolve(null);
    });

    render(
      <Wrapper>
        <ComplianceDocumentUploadDialog
          open
          onOpenChange={onOpenChange}
          document={buildDocument()}
        />
      </Wrapper>,
    );
    const input = screen.getByTestId(
      "compliance-document-upload-input",
    ) as HTMLInputElement;
    const file = await fileFromBytes(
      "ok.pdf",
      "application/pdf",
      new Uint8Array([9]),
    );
    await user.upload(input, file);
    await user.click(screen.getByRole("button", { name: "Загрузить" }));

    await waitFor(() => {
      expect(screen.getByText("Не удалось загрузить файл")).toBeInTheDocument();
    });
    expect(onOpenChange).not.toHaveBeenCalled();
  });
});
