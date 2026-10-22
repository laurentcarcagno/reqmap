"use client";

import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, ChevronsDownUp, ChevronsUpDown } from "lucide-react";
import { toast } from "sonner";
import { api, type Node, type ApplicabilityValue, type ConformityValue } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ApplicabilitySelect } from "./applicability-select";
import { ConformitySelect } from "./conformity-select";
import { CommentCell } from "./comment-cell";
import { DescriptionCell } from "./description-cell";

const MIN_COLUMN_WIDTH = 48;

/** Header columns. `auto` sizes them to their content until the user first drags a handle. */
const COLUMNS = [
  { label: "#", auto: "w-12", fallback: 56 },
  { label: "ID / Section", auto: "w-px whitespace-nowrap", fallback: 130 },
  { label: "Title", auto: "w-px whitespace-nowrap", fallback: 260 },
  { label: "Description", auto: "w-[44%]", fallback: 420, shared: "hidden lg:table-cell" },
  { label: "Applicability", auto: "w-28", fallback: 112 },
  { label: "Conformity", auto: "w-32", fallback: 128 },
  { label: "Comment", auto: "w-[33%] min-w-64", fallback: 300 },
] as const;
const DESCRIPTION_INDEX = 3;

interface NodeTableProps {
  documentId: string;
  expandAll: boolean;
  onExpandAllChange: (expandAll: boolean) => void;
}

export function NodeTable({ documentId, expandAll, onExpandAllChange }: NodeTableProps) {
  const queryClient = useQueryClient();
  // null: columns size themselves; after the first drag every column gets a fixed pixel width
  const [widths, setWidths] = useState<number[] | null>(null);
  const headRefs = useRef<(HTMLTableCellElement | null)[]>([]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["nodes", documentId],
    queryFn: () => api.nodes.list(documentId, { limit: 500 }),
    enabled: !!documentId,
  });

  const { mutate: updateNode } = useMutation({
    mutationFn: ({
      nodeId,
      patch,
    }: {
      nodeId: string;
      patch: { applicability?: ApplicabilityValue; conformity?: ConformityValue; comment?: string; description?: string };
    }) => api.nodes.update(nodeId, patch),
    onMutate: async ({ nodeId, patch }) => {
      await queryClient.cancelQueries({ queryKey: ["nodes", documentId] });
      const previous = queryClient.getQueryData(["nodes", documentId]);
      queryClient.setQueryData(["nodes", documentId], (old: typeof data) => {
        if (!old) return old;
        return {
          ...old,
          data: old.data.map((n: Node) =>
            n.id === nodeId ? { ...n, ...patch } : n,
          ),
        };
      });
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["nodes", documentId], context.previous);
      }
      toast.error("Failed to update node");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["nodes", documentId] });
    },
  });

  const nodes = data?.data ?? [];

  function startResize(index: number, e: React.PointerEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    const handle = e.currentTarget;
    handle.setPointerCapture(e.pointerId);
    const current =
      widths ??
      COLUMNS.map((column, i) => Math.round(headRefs.current[i]?.getBoundingClientRect().width || column.fallback));
    setWidths(current);
    const startX = e.clientX;
    const startWidth = current[index] ?? MIN_COLUMN_WIDTH;
    const onMove = (move: PointerEvent) =>
      setWidths((prev) =>
        prev ? prev.map((w, i) => (i === index ? Math.max(MIN_COLUMN_WIDTH, startWidth + move.clientX - startX) : w)) : prev,
      );
    const onUp = () => {
      handle.removeEventListener("pointermove", onMove);
      handle.removeEventListener("pointerup", onUp);
    };
    handle.addEventListener("pointermove", onMove);
    handle.addEventListener("pointerup", onUp);
  }

  const resized = widths !== null;
  const total = widths?.reduce((sum, w) => sum + w, 0) ?? 0;
  const tableStyle = widths
    ? ({
        tableLayout: "fixed",
        "--w-all": `${total}px`,
        "--w-no-desc": `${total - (widths[DESCRIPTION_INDEX] ?? 0)}px`,
      } as React.CSSProperties)
    : undefined;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12 gap-3 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        <span className="text-sm">Loading nodes…</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center p-12 gap-3 text-destructive">
        <AlertCircle className="h-5 w-5" aria-hidden="true" />
        <span className="text-sm">Failed to load nodes</span>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center p-12 text-muted-foreground">
        <span className="text-sm">No nodes found</span>
      </div>
    );
  }

  return (
    // No overflow here: the header sticks to the scroll container of the document viewer
    <div className="w-full">
      <table
        className={cn(
          "border-collapse text-sm",
          resized ? "w-[var(--w-no-desc)] lg:w-[var(--w-all)] [&_td]:overflow-hidden" : "w-full",
        )}
        style={tableStyle}
        aria-label="Requirement nodes"
      >
        <thead>
          <tr className="border-b border-border bg-deep">
            {COLUMNS.map((column, i) => (
              <th
                key={column.label}
                ref={(el) => {
                  headRefs.current[i] = el;
                }}
                scope="col"
                style={widths ? { width: widths[i] } : undefined}
                className={cn(
                  "hem-label sticky top-0 z-10 bg-deep px-3 py-2.5 text-left text-deep-foreground",
                  !resized && column.auto,
                  "shared" in column && column.shared,
                )}
              >
                {i === DESCRIPTION_INDEX ? (
                  <div className="flex items-center gap-1.5">
                    <span>Description</span>
                    <button
                      type="button"
                      onClick={() => onExpandAllChange(!expandAll)}
                      className="inline-flex items-center gap-1 px-1 py-0.5 text-[10px] text-deep-foreground/70 hover:bg-white/10 hover:text-deep-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring transition-colors"
                      aria-label={expandAll ? "Collapse all descriptions" : "Expand all descriptions"}
                      title={expandAll ? "Collapse all" : "Expand all"}
                    >
                      {expandAll
                        ? <><ChevronsDownUp className="h-3 w-3" aria-hidden="true" /><span>Collapse all</span></>
                        : <><ChevronsUpDown className="h-3 w-3" aria-hidden="true" /><span>Expand all</span></>}
                    </button>
                  </div>
                ) : (
                  column.label
                )}
                <div
                  role="separator"
                  aria-orientation="vertical"
                  aria-label={`Resize ${column.label} column (double-click to reset)`}
                  title="Drag to resize · double-click to reset"
                  onPointerDown={(e) => startResize(i, e)}
                  onDoubleClick={() => setWidths(null)}
                  className="absolute right-0 top-0 h-full w-1.5 cursor-col-resize touch-none select-none hover:bg-white/30"
                />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => (
            <tr
              key={node.id}
              className={cn(
                "border-b border-border transition-colors",
                node.type === "title"
                  ? "bg-selection/60 hover:bg-selection font-medium"
                  : "hover:bg-accent",
              )}
            >
              <td className="px-3 py-2 font-mono text-muted-foreground">{node.order}</td>
              <td className="px-3 py-2 whitespace-nowrap">
                {node.type === "title" ? (
                  <span className="font-mono text-xs text-muted-foreground">{node.section}</span>
                ) : (
                  <span className="font-mono text-xs text-deep dark:text-foreground">{node.req_id}</span>
                )}
              </td>
              <td className="px-3 py-2 whitespace-nowrap">
                <span
                  title={node.title}
                  className={cn(
                    node.type === "title"
                      ? "font-semibold text-foreground"
                      : "text-foreground",
                  )}
                >
                  {node.title}
                </span>
              </td>
              <td className={cn("px-3 py-2 hidden lg:table-cell", !resized && "max-w-0")}>
                {node.type === "requirement" && (
                  <DescriptionCell
                    text={node.description}
                    expandAll={expandAll}
                    onSave={(description) => updateNode({ nodeId: node.id, patch: { description } })}
                  />
                )}
              </td>
              <td className="px-3 py-2">
                {node.applicability === "T" ? (
                  <span className="font-mono text-xs text-muted-foreground">T</span>
                ) : (
                  <ApplicabilitySelect
                    value={node.applicability}
                    onChange={(v) => updateNode({ nodeId: node.id, patch: { applicability: v } })}
                  />
                )}
              </td>
              <td className="px-3 py-2">
                {node.conformity === "T" ? (
                  <span className="font-mono text-xs text-muted-foreground">T</span>
                ) : (
                  <ConformitySelect
                    value={node.conformity}
                    onChange={(v) => updateNode({ nodeId: node.id, patch: { conformity: v } })}
                  />
                )}
              </td>
              <td className="px-3 py-2">
                {node.type === "requirement" && (
                  <CommentCell
                    value={node.comment}
                    onSave={(comment) => updateNode({ nodeId: node.id, patch: { comment } })}
                  />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
