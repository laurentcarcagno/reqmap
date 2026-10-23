import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { NodeTable } from "./node-table";

vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

// jsdom has no ResizeObserver; DescriptionCell uses one to detect truncated text.
vi.stubGlobal(
  "ResizeObserver",
  class {
    observe() {}
    disconnect() {}
  },
);

vi.mock("@/lib/api", () => ({
  api: {
    nodes: {
      list: vi.fn().mockResolvedValue({
        data: [
          { id: "t1", order: 1, type: "title", section: "4.1", title: "General Requirements", description: "", applicability: "T", conformity: "T", comment: "" },
          { id: "r1", order: 2, type: "requirement", req_id: "S2NG-THW-2252//R", title: "", description: "Degradation factor", applicability: "A", conformity: "C", comment: "" },
        ],
      }),
      update: vi.fn(),
    },
  },
}));

function renderTable() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <NodeTable documentId="doc-1" expandAll={false} onExpandAllChange={vi.fn()} />
    </QueryClientProvider>,
  );
}

describe("NodeTable", () => {
  it("hides and shows all the title rows", async () => {
    renderTable();
    const user = userEvent.setup();
    expect(await screen.findByText("General Requirements")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Hide titles" }));

    expect(screen.queryByText("General Requirements")).not.toBeInTheDocument();
    expect(screen.getByText("S2NG-THW-2252//R")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Show titles" }));

    expect(screen.getByText("General Requirements")).toBeInTheDocument();
  });

  it("hides and shows the selected column", async () => {
    renderTable();
    const user = userEvent.setup();
    await screen.findByText("S2NG-THW-2252//R");
    expect(screen.getByRole("button", { name: "Hide column" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "ID / Section" }));
    await user.click(screen.getByRole("button", { name: "Hide “ID / Section” column" }));

    expect(screen.queryByText("S2NG-THW-2252//R")).not.toBeInTheDocument();
    // The hidden column stays selected, as a strip that can be selected again after a deselect.
    await user.click(screen.getByRole("button", { name: "ID / Section" }));
    expect(screen.getByRole("button", { name: "Hide column" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "ID / Section" }));
    await user.click(screen.getByRole("button", { name: "Show “ID / Section” column" }));

    expect(screen.getByText("S2NG-THW-2252//R")).toBeInTheDocument();
  });
});
