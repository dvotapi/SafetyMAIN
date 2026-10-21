import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { ComplianceDocumentTagInput } from "@/features/compliance-documents/components/compliance-document-tag-input";

afterEach(cleanup);

function Host({ initial = [] as string[] }) {
  const [values, setValues] = useState<string[]>(initial);
  return (
    <ComplianceDocumentTagInput
      id="tags"
      values={values}
      onChange={setValues}
    />
  );
}

describe("ComplianceDocumentTagInput", () => {
  it("adds a tag on Enter", async () => {
    const user = userEvent.setup();
    render(<Host />);
    const input = screen.getByPlaceholderText(
      "Введите значение и Enter",
    ) as HTMLInputElement;
    await user.type(input, "Электрик{Enter}");
    expect(screen.getByText("Электрик")).toBeInTheDocument();
    expect(input.value).toBe("");
  });

  it("de-duplicates existing values", async () => {
    const user = userEvent.setup();
    render(<Host initial={["A"]} />);
    const input = screen.getByPlaceholderText("Введите значение и Enter");
    await user.type(input, "A{Enter}");
    expect(screen.getAllByText("A")).toHaveLength(1);
  });

  it("removes last tag on Backspace in empty input", async () => {
    const user = userEvent.setup();
    render(<Host initial={["A", "B"]} />);
    const input = screen.getByPlaceholderText("Введите значение и Enter");
    input.focus();
    await user.keyboard("{Backspace}");
    expect(screen.queryByText("B")).not.toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
  });
});
