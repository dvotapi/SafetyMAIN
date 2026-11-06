import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PdfViewer } from "@/components/document-viewer";

const pdfjs = vi.hoisted(() => {
  const destroy = vi.fn();
  const getDocument = vi.fn(
    (options: { url: string; disableRange: boolean }) => ({
      url: options.url,
      promise: Promise.resolve({
        numPages: 3,
        destroy,
        getPage: vi.fn(async () => ({
          getViewport: ({ scale }: { scale: number }) => ({
            width: 600 * scale,
            height: 800 * scale,
          }),
          render: () => ({ promise: Promise.resolve() }),
        })),
      }),
    }),
  );
  return { getDocument, destroy, GlobalWorkerOptions: { workerSrc: "" } };
});

vi.mock("pdfjs-dist", () => pdfjs);

afterEach(() => {
  cleanup();
  pdfjs.getDocument.mockClear();
});

describe("PdfViewer", () => {
  it("loads a PDF lazily with one plain GET and pages with buttons and keys", async () => {
    render(
      <PdfViewer
        url="https://storage.test/scan.pdf"
        contentType="application/pdf"
        title="Скан"
      />,
    );

    expect(await screen.findByText("Страница 1 из 3")).toBeInTheDocument();
    expect(pdfjs.getDocument).toHaveBeenCalledWith({
      url: "https://storage.test/scan.pdf",
      disableRange: true,
      disableStream: true,
    });
    expect(
      screen.getAllByRole("button", { name: /^Страница \d$/ }),
    ).toHaveLength(3);

    await userEvent.click(
      screen.getByRole("button", { name: "Следующая страница" }),
    );
    expect(screen.getByText("Страница 2 из 3")).toBeInTheDocument();

    const region = screen.getByRole("region", { name: "Просмотр: Скан" });
    region.focus();
    fireEvent.keyDown(region, { key: "End" });
    expect(screen.getByText("Страница 3 из 3")).toBeInTheDocument();
    fireEvent.keyDown(region, { key: "ArrowLeft" });
    expect(screen.getByText("Страница 2 из 3")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Страница 1" }));
    expect(screen.getByRole("button", { name: "Страница 1" })).toHaveAttribute(
      "aria-current",
      "page",
    );

    await userEvent.click(screen.getByRole("button", { name: "Увеличить" }));
    expect(screen.getByText("125%")).toBeInTheDocument();
  });

  it("shows images directly and does not load pdf.js", () => {
    render(
      <PdfViewer
        url="https://storage.test/scan.png"
        contentType="image/png"
        title="Скан"
      />,
    );

    expect(screen.getByRole("img", { name: "Скан" })).toHaveAttribute(
      "src",
      "https://storage.test/scan.png",
    );
    expect(pdfjs.getDocument).not.toHaveBeenCalled();
  });

  it("offers only a download for other types", async () => {
    const onDownload = vi.fn();
    render(
      <PdfViewer
        url="https://storage.test/act.docx"
        contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        title="Акт"
        onDownload={onDownload}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Скачать" }));
    expect(onDownload).toHaveBeenCalled();
  });

  it("reports a file that cannot be opened", async () => {
    pdfjs.getDocument.mockImplementationOnce((options) => ({
      url: options.url,
      promise: Promise.reject(new Error("bad")),
    }));
    render(
      <PdfViewer
        url="https://storage.test/x.pdf"
        contentType="application/pdf"
        title="X"
      />,
    );

    await waitFor(() =>
      expect(screen.getByText("Не удалось открыть PDF.")).toBeInTheDocument(),
    );
  });

  it("waits for the URL", () => {
    render(<PdfViewer url={null} contentType="application/pdf" title="X" />);

    expect(pdfjs.getDocument).not.toHaveBeenCalled();
  });
});
