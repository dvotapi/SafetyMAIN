import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { cleanup, render, screen } from "@testing-library/react";
import { useForm } from "react-hook-form";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ComplianceDocumentForm } from "@/features/compliance-documents/components/compliance-document-form";
import {
  complianceDocumentFormSchema,
  defaultComplianceDocumentFormValues,
  type ComplianceDocumentFormValues,
} from "@/features/compliance-documents/schemas/compliance-document-form-schema";
import type { DocumentTypeDto } from "@/features/compliance-documents/types/compliance-documents-dto";
import { apiClient } from "@/services/api/client";

vi.mock("@/hooks/auth", () => ({
  useAuth: () => ({ hasPermission: () => true }),
  useOrganization: () => ({
    organizationId: "org-1",
    organizationName: "Org",
    membership: null,
  }),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const TYPE: DocumentTypeDto = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  organization_id: "org-1",
  code: "local_act",
  title_ru: "Локальный акт",
  safety_domain: "occupational",
  subject_kind: "organization",
  review_period_months: 36,
  validity_months: null,
  periodicity_months: null,
  warning_thresholds_days: [30],
  requires_acknowledgement: false,
  requires_approval_order: true,
  legal_basis: "ТК РФ",
  legal_basis_reference: null,
  is_active: true,
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};

function Host({
  onSubmit,
  initial = defaultComplianceDocumentFormValues,
}: {
  onSubmit: (values: ComplianceDocumentFormValues) => void;
  initial?: ComplianceDocumentFormValues;
}) {
  const form = useForm<ComplianceDocumentFormValues>({
    resolver: zodResolver(complianceDocumentFormSchema),
    defaultValues: initial,
    mode: "onSubmit",
  });
  return (
    <ComplianceDocumentForm
      id="test-form"
      form={form}
      onSubmit={onSubmit}
      types={[TYPE]}
    />
  );
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("ComplianceDocumentForm", () => {
  it("blocks submit when required fields are empty", async () => {
    const onSubmit = vi.fn();
    vi.spyOn(apiClient, "request").mockResolvedValue({
      items: [],
      pagination: { total: 0, offset: 0, limit: 50 },
    });

    render(
      <Wrapper>
        <Host onSubmit={onSubmit} />
      </Wrapper>,
    );

    const form = document.getElementById("test-form") as HTMLFormElement;
    form.requestSubmit();
    await screen.findAllByText(/Выберите тип документа/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits valid values trimmed", async () => {
    const onSubmit = vi.fn();
    vi.spyOn(apiClient, "request").mockResolvedValue({
      items: [],
      pagination: { total: 0, offset: 0, limit: 50 },
    });

    render(
      <Wrapper>
        <Host
          onSubmit={onSubmit}
          initial={{
            ...defaultComplianceDocumentFormValues,
            document_type_id: TYPE.id,
            code: "CD-001",
            title: "Положение об охране труда",
          }}
        />
      </Wrapper>,
    );

    const form = document.getElementById("test-form") as HTMLFormElement;
    form.requestSubmit();

    // Wait a tick for RHF.
    await new Promise((r) => setTimeout(r, 0));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const [values] = onSubmit.mock.calls[0] as [ComplianceDocumentFormValues];
    expect(values.code).toBe("CD-001");
    expect(values.title).toBe("Положение об охране труда");
    expect(values.document_type_id).toBe(TYPE.id);
  });
});
