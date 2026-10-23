import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Sidebar } from "@/components/layout/sidebar";
import { UploadDialog } from "./upload-dialog";

const { upload, toastError } = vi.hoisted(() => ({ upload: vi.fn(), toastError: vi.fn() }));

vi.mock("sonner", () => ({ toast: { error: toastError, success: vi.fn() } }));

vi.mock("@/lib/api", () => ({
  api: {
    customers: { list: vi.fn().mockResolvedValue({ data: [{ id: "airbus", label: "Airbus" }] }) },
    documents: {
      list: vi.fn().mockResolvedValue({ data: [] }),
      get: vi.fn((id: string) =>
        Promise.resolve({
          id,
          original_filename: `${id}.pdf`,
          status: "completed",
          requirement_count: 3,
          title_count: 1,
        }),
      ),
      upload,
    },
  },
}));

function pdf(name: string): File {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" });
}

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

beforeEach(() => {
  upload.mockReset();
  toastError.mockReset();
  upload.mockImplementation((file: File) => Promise.resolve({ id: file.name.replace(".pdf", "") }));
});

describe("UploadDialog", () => {
  it("uploads several files one after the other with the same customer and table mode", async () => {
    renderWithClient(
      <UploadDialog open onOpenChange={vi.fn()} initialFiles={[pdf("a.pdf"), pdf("b.pdf")]} />,
    );
    const user = userEvent.setup();

    const files = within(screen.getByRole("list", { name: "Selected files" }));
    expect(files.getByText("a.pdf")).toBeInTheDocument();
    expect(files.getByText("b.pdf")).toBeInTheDocument();

    await user.selectOptions(await screen.findByLabelText("Customer"), "airbus");
    await user.click(screen.getByRole("radio", { name: "HTML" }));
    await user.click(screen.getByRole("button", { name: "Upload 2 files" }));

    // The second file is only sent once the first one has been processed.
    await waitFor(() => expect(upload).toHaveBeenCalledTimes(1));
    expect(upload.mock.calls[0]![0].name).toBe("a.pdf");
    await waitFor(() => expect(upload).toHaveBeenCalledTimes(2), { timeout: 5000 });
    expect(upload.mock.calls[1]![0].name).toBe("b.pdf");
    expect(upload.mock.calls.map((c) => c.slice(1))).toEqual([
      ["airbus", "html"],
      ["airbus", "html"],
    ]);
    expect(await screen.findByText(/File 2 of 2 · b\.pdf/)).toBeInTheDocument();
  });

  it("lets a selected file be removed", async () => {
    renderWithClient(
      <UploadDialog open onOpenChange={vi.fn()} initialFiles={[pdf("a.pdf"), pdf("b.pdf")]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Remove a.pdf" }));

    expect(screen.queryByText("a.pdf")).not.toBeInTheDocument();
    expect(screen.getByText("b.pdf")).toBeInTheDocument();
  });
});

describe("Sidebar upload button", () => {
  function dropOnUploadButton(files: File[]) {
    fireEvent.drop(screen.getByRole("button", { name: "Upload document" }), {
      dataTransfer: { files, types: ["Files"] },
    });
  }

  it("opens the upload dialog with the dropped PDF files", async () => {
    renderWithClient(
      <Sidebar selectedDocumentId={null} onSelectDocument={vi.fn()} onDocumentDeleted={vi.fn()} />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    dropOnUploadButton([pdf("a.pdf"), pdf("b.pdf")]);

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("a.pdf")).toBeInTheDocument();
    expect(within(dialog).getByText("b.pdf")).toBeInTheDocument();
  });

  it("ignores dropped files that are not PDFs", async () => {
    renderWithClient(
      <Sidebar selectedDocumentId={null} onSelectDocument={vi.fn()} onDocumentDeleted={vi.fn()} />,
    );

    dropOnUploadButton([new File(["x"], "notes.txt", { type: "text/plain" }), pdf("a.pdf")]);

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("a.pdf")).toBeInTheDocument();
    expect(within(dialog).queryByText("notes.txt")).not.toBeInTheDocument();
    expect(toastError).toHaveBeenCalledWith("1 non-PDF file(s) ignored");
  });

  it("does not open the dialog when nothing dropped is a PDF", () => {
    renderWithClient(
      <Sidebar selectedDocumentId={null} onSelectDocument={vi.fn()} onDocumentDeleted={vi.fn()} />,
    );

    dropOnUploadButton([new File(["x"], "notes.txt", { type: "text/plain" })]);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(toastError).toHaveBeenCalledWith("Only PDF files are accepted");
  });
});
